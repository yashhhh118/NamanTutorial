from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import sqlite3
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Load environment variables from .env file
load_dotenv()

from datetime import timedelta
# ==========================================
# INPUT VALIDATION FUNCTIONS
# ==========================================

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate Indian phone number (10 digits, starts with 6-9)"""
    # Remove spaces, dashes, and common prefixes
    phone = phone.strip().replace(' ', '').replace('-', '')
    if phone.startswith('+91'):
        phone = phone[3:]
    elif phone.startswith('0') and len(phone) > 10:
        phone = phone[1:]
        
    pattern = r'^[6-9]\d{9}$'
    return re.match(pattern, phone) is not None

def validate_username(username):
    """Username: 3-20 chars, alphanumeric + underscore"""
    username = username.strip()
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

def validate_password(password):
    """Password minimum 6 characters"""
    if len(password) < 6:
        return False
    return True

def validate_name(name):
    """Name should be 2-50 characters, letters and spaces only"""
    name = name.strip()
    if len(name) < 2 or len(name) > 50:
        return False
    if not re.match(r"^[a-zA-Z\s'-]+$", name):
        return False
    return True

def validate_pincode(pincode):
    """Validate Indian pincode (6 digits)"""
    pincode = pincode.strip()
    pattern = r'^\d{6}$'
    return re.match(pattern, pincode) is not None

# ==========================================
# FLASK APP SETUP
# ==========================================

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24)) # CHANGE THIS LINE

# ==========================================
# SESSION CONFIGURATION (SECURITY)
# ==========================================

app.config['SESSION_COOKIE_SECURE'] = True  # Only send over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # JavaScript can't access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Prevent CSRF attacks
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session expires after 7 days

@app.before_request
def make_session_permanent():
    """Make session permanent so timeout works"""
    session.permanent = True

DATABASE = 'tutors.db'
APPLICANTS_DB = 'tutor_applications.db'

def init_db():
    """Initializes SQLite databases."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tutor_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                subject TEXT NOT NULL,
                grade TEXT,
                pincode TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                student_name TEXT NOT NULL,
                parent_name TEXT,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                class_grade TEXT,
                school_name TEXT,
                address TEXT,
                avatar TEXT,
                subject TEXT,
                time TEXT,
                tuition_place TEXT,
                tuition_details TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tutors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                photo_url TEXT NOT NULL,
                experience TEXT NOT NULL,
                rating REAL
            )
        ''')
        
        # Seed dummy tutors if table is empty
        cursor.execute("SELECT COUNT(*) FROM tutors")
        if cursor.fetchone()[0] == 0:
            mock_tutors = [
                ('Priya Sharma', 'Mathematics & Science', 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&h=400&fit=crop', '5 Years exp.', 4.9),
                ('Rajesh Kumar', 'Physics', 'https://images.unsplash.com/photo-1568602471122-7832951cc4c5?w=400&h=400&fit=crop', '8 Years exp.', 4.8),
                ('Sneha Desai', 'English', 'https://images.unsplash.com/photo-1580894732444-8ecded7900b7?w=400&h=400&fit=crop', '4 Years exp.', 4.7),
                ('Amit Patel', 'Social Studies', 'https://images.unsplash.com/photo-1544717302-de2939b7ef71?w=400&h=400&fit=crop', '6 Years exp.', 4.9),
                ('Neha Joshi', 'Hindi & Marathi', 'https://images.unsplash.com/photo-1598550874175-4d0ef436c909?w=400&h=400&fit=crop', '7 Years exp.', 5.0),
                ('Vikram Singh', 'Computer Science', 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400&h=400&fit=crop', '3 Years exp.', 4.6),
            ]
            cursor.executemany("INSERT INTO tutors (name, subject, photo_url, experience, rating) VALUES (?, ?, ?, ?, ?)", mock_tutors)
        
        conn.commit()

    with sqlite3.connect(APPLICANTS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applicants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                cv_file_path TEXT NOT NULL,
                status TEXT DEFAULT 'Pending Review',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# Guarantee the databases are initialized before Gunicorn hits any web routes
init_db()

@app.route('/book-tutor')
def book_tutor():
    """Renders the tutor selection page if logged in."""
    if not session.get('user'):
        return redirect(url_for('book_demo'))
        
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tutors")
        tutors = cursor.fetchall()
        
    return render_template('book_tutor.html', tutors=tutors)

@app.route('/')
def index():
    """Renders the main homepage."""
    return render_template('index.html')

@app.route('/about')
def about():
    """Renders the about us page."""
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles existing student/parent logins across multiple identifiers."""
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        
        # ==========================================
        # VALIDATE INPUTS
        # ==========================================
        
        # Check if fields are empty
        if not identifier:
            return render_template('login.html', error="❌ Please enter your username, email, or phone number")
        
        if not password:
            return render_template('login.html', error="❌ Please enter your password")
        
        # ==========================================
        # AUTHENTICATE USER
        # ==========================================
        
        try:
            with sqlite3.connect(DATABASE) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM users 
                    WHERE (username=? OR student_name=? OR email=? OR phone=?)
                ''', (identifier, identifier, identifier, identifier))
                user = cursor.fetchone()
                
                # Check if user exists and password matches
                if user:
                    if user['password'].startswith(('scrypt:', 'pbkdf2:')) and check_password_hash(user['password'], password):
                        is_valid = True
                    elif user['password'] == password:
                        is_valid = True
                    else:
                        is_valid = False

                    if is_valid:
                        session['user'] = dict(user)
                        print(f"✅ User logged in: {identifier}")
                        return redirect(url_for('index'))
                    else:
                        print(f"❌ Failed login attempt for: {identifier}")
                        return render_template('login.html', error="❌ Invalid username/email or password. Please try again.")
                else:
                    return render_template('login.html', error="❌ Invalid username/email or password. Please try again.")
        
        except Exception as e:
            print(f"Login error: {str(e)}")
            return render_template('login.html', error="❌ Login failed. Please try again later.")
                
    return render_template('login.html')

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template('contact.html')

@app.route('/book-demo', methods=['GET', 'POST'])
def book_demo():
    """Renders the book free demo page and handles registration submission."""
    if request.method == 'POST':
        form_data = request.form.to_dict()
        
        # ==========================================
        # VALIDATE ALL INPUTS
        # ==========================================
        
        # Validate username
        username = form_data.get('username', '').strip()
        if not validate_username(username):
            return render_template('book_demo.html', error="Username must be 3-20 characters (letters, numbers, underscore only)")
        
        # Validate password
        password = form_data.get('password', '')
        if not validate_password(password):
            return render_template('book_demo.html', error="Password must be at least 6 characters")
        
        # Validate email
        email = form_data.get('email', '').strip()
        if not validate_email(email):
            return render_template('book_demo.html', error="Please enter a valid email address")
        
        # Validate phone
        phone = form_data.get('phone', '').strip()
        if not validate_phone(phone):
            return render_template('book_demo.html', error="Please enter a valid 10-digit Indian phone number (starting with 6-9)")
        
        # Validate student name
        student_name = form_data.get('student_name', '').strip()
        if not validate_name(student_name):
            return render_template('book_demo.html', error="Student name must be 2-50 characters (letters and spaces only)")
        
        # Validate parent name
        parent_name = form_data.get('parent_name', '').strip()
        if parent_name and not validate_name(parent_name):
            return render_template('book_demo.html', error="Parent name must be 2-50 characters (letters and spaces only)")
        
        # Validate address
        address = form_data.get('address', '').strip()
        if not address or len(address) < 5:
            return render_template('book_demo.html', error="Please enter a valid address")
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Prepare user data
        user_dict = {
            'username': username,
            'password': hashed_password,
            'avatar': form_data.get('avatar', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix'),
            'student_name': student_name,
            'parent_name': parent_name,
            'phone': phone,
            'email': email,
            'class_grade': form_data.get('class_grade', ''),
            'school_name': form_data.get('school_name', '').strip(),
            'address': address,
            'subject': form_data.get('subject', '').strip(),
            'time': form_data.get('time', ''),
            'tuition_place': ", ".join(request.form.getlist('tuition_place')), 
            'tuition_details': form_data.get('tuition_details', '').strip()
        }
        
        try:
            # Store in database
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password, student_name, parent_name, phone, email, class_grade, school_name, address, avatar, subject, time, tuition_place, tuition_details)
                    VALUES (:username, :password, :student_name, :parent_name, :phone, :email, :class_grade, :school_name, :address, :avatar, :subject, :time, :tuition_place, :tuition_details)
                ''', user_dict)
                conn.commit()
            
            session['user'] = user_dict
            return redirect(url_for('index'))
            
        except sqlite3.IntegrityError as e:
            error_str = str(e).lower()
            
            # Check which field caused the error
            if 'username' in error_str:
                return render_template('book_demo.html', error="❌ This username is already taken. Please choose a different username.")
            elif 'email' in error_str:
                return render_template('book_demo.html', error="❌ This email is already registered. Please login instead or use a different email.")
            else:
                return render_template('book_demo.html', error="❌ Registration failed. Please try again with different details.")
        
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return render_template('book_demo.html', error="❌ An error occurred during registration. Please try again.")
        except Exception as e:
            return render_template('book_demo.html', error=f"Registration error: Please try again")
    
    return render_template('book_demo.html')

@app.route('/logout')
def logout():
    """Clears the session."""
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/become-tutor')
def become_tutor():
    """Renders the become a tutor page."""
    return render_template('become_tutor.html')

import os
from werkzeug.utils import secure_filename
import smtplib
from email.message import EmailMessage

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ==========================================
# EMAIL CONFIGURATION
# ==========================================
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL')

@app.route('/submit-application', methods=['POST'])
def submit_application():
    """Handles CV upload and sends an ACTUAL email via Gmail SMTP."""
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    cv_file = request.files.get('cv_file')
    
    # ==========================================
    # VALIDATE INPUTS
    # ==========================================
    
    # Validate name
    if not validate_name(name):
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'Invalid Name!',
                text: 'Please enter a valid name (2-50 characters, letters only)',
                icon: 'error',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Go Back'
            }).then(() => {
                window.history.back();
            });
        </script>
        ''', 400
    
    # Validate phone
    if not validate_phone(phone):
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'Invalid Phone Number!',
                text: 'Please enter a valid 10-digit Indian phone number',
                icon: 'error',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Go Back'
            }).then(() => {
                window.history.back();
            });
        </script>
        ''', 400
    
    # Validate CV file
    if not cv_file or cv_file.filename == '':
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'No File Selected!',
                text: 'Please select a CV file to upload',
                icon: 'error',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Go Back'
            }).then(() => {
                window.history.back();
            });
        </script>
        ''', 400
    
    # Validate file type (only PDF, DOC, DOCX)
    allowed_extensions = {'pdf', 'doc', 'docx'}
    file_ext = cv_file.filename.rsplit('.', 1)[1].lower() if '.' in cv_file.filename else ''
    
    if file_ext not in allowed_extensions:
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'Invalid File Type!',
                text: 'Only PDF, DOC, and DOCX files are allowed',
                icon: 'error',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Go Back'
            }).then(() => {
                window.history.back();
            });
        </script>
        ''', 400
    
    # Validate file size (max 5MB)
    cv_file.seek(0, 2)  # Seek to end
    file_size = cv_file.tell()
    cv_file.seek(0)  # Seek back to start
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'File Too Large!',
                text: 'File size must be less than 5MB',
                icon: 'error',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Go Back'
            }).then(() => {
                window.history.back();
            });
        </script>
        ''', 400
    
    # ==========================================
    # ALL VALIDATIONS PASSED - PROCEED
    # ==========================================
    
    
    filename = secure_filename(cv_file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{name.replace(' ', '_')}_{filename}")
    cv_file.save(file_path)
        
    # Save to separate Tutor Applications Database
    with sqlite3.connect(APPLICANTS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
                INSERT INTO applicants (name, phone, cv_file_path)
                VALUES (?, ?, ?)
            ''', (name, phone, file_path))
        conn.commit()
        
        # Build the actual email message
        msg = EmailMessage()
        msg['Subject'] = f"🚀 New Tutor Application: {name}"
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        
        # Email Body
        msg.set_content(f"""
        New Tutor Application Received!
        
        Applicant Name: {name}
        WhatsApp Number: {phone}
        
        Please find their attached CV document containing their salary, hours, and experience expectations.
        """)
        
        # Attach the CV PDF/DOCX Document
        import mimetypes
        ctype, encoding = mimetypes.guess_type(file_path)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        
        with open(file_path, 'rb') as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=filename)

        # Attempt to Send the Email safely
        error_msg = None
        try:
            if SENDER_EMAIL != "your-email@gmail.com":
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
                    smtp.send_message(msg)
                print("📧 REAL EMAIL SENT SUCCESSFULLY!")
            else:
                print("⚠️ APP PASSWORD NOT CONFIGURED YET! Email skipped.")
        except Exception as e:
            error_msg = str(e)
            print(f"FAILED TO SEND EMAIL: {error_msg}")
        
        # Show Success pop-up directly back to the user
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'Application Sent to Host!',
                text: 'Your CV and details have been successfully uploaded!',
                icon: 'success',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Return Home'
            }).then(() => {
                window.location.href = "/";
            });
        </script>
        '''
    return "Invalid form or file.", 400

@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    """Handles contact form submissions and sends an email."""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    message = request.form.get('message', '').strip()
    
    # ==========================================
    # VALIDATE INPUTS
    # ==========================================
    
    # Validate name
    if not validate_name(name):
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'Invalid Name!',
                text: 'Please enter a valid name (2-50 characters, letters only)',
                icon: 'error',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Go Back'
            }).then(() => {
                window.history.back();
            });
        </script>
        ''', 400
    
    # Validate email
    if not validate_email(email):
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'Invalid Email!',
                text: 'Please enter a valid email address',
                icon: 'error',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Go Back'
            }).then(() => {
                window.history.back();
            });
        </script>
        ''', 400
    
    # Validate phone (optional but if provided, must be valid)
    if phone and not validate_phone(phone):
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'Invalid Phone Number!',
                text: 'Please enter a valid 10-digit Indian phone number',
                icon: 'error',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Go Back'
            }).then(() => {
                window.history.back();
            });
        </script>
        ''', 400
    
    # Validate message length (minimum 10 characters, maximum 1000)
    if not message or len(message) < 10:
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'Message Too Short!',
                text: 'Please write a message with at least 10 characters',
                icon: 'error',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Go Back'
            }).then(() => {
                window.history.back();
            });
        </script>
        ''', 400
    
    if len(message) > 1000:
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'Message Too Long!',
                text: 'Please keep your message under 1000 characters',
                icon: 'error',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Go Back'
            }).then(() => {
                window.history.back();
            });
        </script>
        ''', 400
    
    # ==========================================
    # ALL VALIDATIONS PASSED - PROCEED
    # ==========================================
    
    # Build email message
    msg = EmailMessage()
    msg['Subject'] = f"💬 New Contact Message from: {name}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    
    msg.set_content(f"""
    New Contact Form Submission Received!
    
    Name: {name}
    Email: {email}
    Phone: {phone}
    
    Message:
    {message}
    """)
    
    # Save to Database
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contact_messages (name, email, phone, message)
                VALUES (?, ?, ?, ?)
            ''', (name, email, phone, message))
            conn.commit()
    except Exception as e:
        print(f"Database error: {str(e)}")
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'Error!',
                text: 'Could not save your message. Please try again.',
                icon: 'error',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Go Back'
            }).then(() => {
                window.history.back();
            });
        </script>
        ''', 500
    
    # Try to send email
    try:
        if SENDER_EMAIL and SENDER_PASSWORD and SENDER_EMAIL != "your-email@gmail.com":
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
                smtp.send_message(msg)
            print("📧 CONTACT EMAIL SENT SUCCESSFULLY!")
        else:
            print("⚠️ EMAIL NOT CONFIGURED YET! Message saved to database.")
    except Exception as e:
        print(f"FAILED TO SEND EMAIL: {str(e)}")
        # Message is still saved in database, so we show success anyway
    
    # Show success message
    return '''
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <body style="background:#f9fafb; font-family:sans-serif;"></body>
    <script>
        Swal.fire({
            title: 'Message Sent!',
            text: 'Thank you for reaching out. We will get back to you shortly.',
            icon: 'success',
            confirmButtonColor: '#111827',
            confirmButtonText: 'Return Home'
        }).then(() => {
            window.location.href = "/";
        });
    </script>
    '''

@app.route('/request-tutor', methods=['POST'])
def request_tutor():
    """Handles API requests to submit tutoring leads."""
    data = request.json if request.is_json else request.form
    
    # Extract data
    name = data.get('name')
    phone = data.get('phone')
    subject = data.get('subject')
    grade = data.get('grade')
    pincode = data.get('pincode')

    # Basic server-side validation
    if not all([name, phone, subject]):
        return jsonify({"error": "Name, phone, and subject are required"}), 400

    try:
        # Insert data into the database
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tutor_requests (name, phone, subject, grade, pincode)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, phone, subject, grade, pincode))
            conn.commit()
            
        return jsonify({"message": "Tutor request submitted successfully!"}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if request.method == 'POST':
        password = request.form.get('password')
        correct_password = os.getenv('ADMIN_PASSWORD')
        if password == correct_password:  # CHANGE THIS LINE
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid password provided.")
    return render_template('admin_login.html')

@app.route('/admin-logout')
def admin_logout():
    """Logs out the admin."""
    session.pop('is_admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_dashboard():
    """Renders the secure admin dashboard."""
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users ORDER BY id DESC")
            students = cursor.fetchall()
        except:
            students = []
            
        try:
            cursor.execute("SELECT * FROM contact_messages ORDER BY timestamp DESC")
            messages = cursor.fetchall()
        except:
            messages = []
            
    with sqlite3.connect(APPLICANTS_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM applicants ORDER BY timestamp DESC")
            applicants = cursor.fetchall()
        except:
            applicants = []

    return render_template('admin_dashboard.html', 
                           students=students, 
                           messages=messages, 
                           applicants=applicants)

@app.route('/admin/download-cv/<int:applicant_id>')
def download_cv(applicant_id):
    """Securely serves the CV file to the admin."""
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    with sqlite3.connect(APPLICANTS_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT cv_file_path FROM applicants WHERE id=?", (applicant_id,))
        applicant = cursor.fetchone()
        
        if applicant and applicant['cv_file_path']:
            filepath = applicant['cv_file_path']
            directory = os.path.abspath(os.path.dirname(filepath))
            filename = os.path.basename(filepath)
            return send_from_directory(directory, filename)
            
    return "File not found", 404

@app.route('/admin/delete/<string:record_type>/<int:record_id>', methods=['POST'])
def admin_delete(record_type, record_id):
    """Deletes a record from the database."""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        if record_type == 'student':
            with sqlite3.connect(DATABASE) as conn:
                conn.cursor().execute("DELETE FROM users WHERE id=?", (record_id,))
                conn.commit()
        elif record_type == 'applicant':
            with sqlite3.connect(APPLICANTS_DB) as conn:
                # Get filepath to optionally delete physical file
                cursor = conn.cursor()
                cursor.execute("SELECT cv_file_path FROM applicants WHERE id=?", (record_id,))
                record = cursor.fetchone()
                if record and record[0] and os.path.exists(record[0]):
                    try:
                        os.remove(record[0])
                    except:
                        pass # if file isn't there or locked
                
                cursor.execute("DELETE FROM applicants WHERE id=?", (record_id,))
                conn.commit()
        elif record_type == 'message':
            with sqlite3.connect(DATABASE) as conn:
                conn.cursor().execute("DELETE FROM contact_messages WHERE id=?", (record_id,))
                conn.commit()
        else:
            return jsonify({'error': 'Invalid record type'}), 400
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run Flask Application on port 5000 in local debug mode
    app.run(debug=True, port=5000)
