from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'super_secret_naman_key_123'

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
                avatar TEXT
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
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users 
                WHERE (username=? OR student_name=? OR email=? OR phone=?) AND password=?
            ''', (identifier, identifier, identifier, identifier, password))
            user = cursor.fetchone()
            
            if user:
                session['user'] = dict(user)
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Invalid credentials. Please check your details and try again.")
                
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
        
        # Secure the data logically simulating a signup
        user_dict = {
            'username': form_data.get('username'),
            'password': form_data.get('password'),
            'avatar': form_data.get('avatar', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix'),
            'student_name': form_data.get('student_name'),
            'parent_name': form_data.get('parent_name'),
            'phone': form_data.get('phone'),
            'email': form_data.get('email'),
            'class_grade': form_data.get('class_grade'),
            'school_name': form_data.get('school_name'),
            'address': form_data.get('address')
        }
        
        try:
            # Store permanently in the database
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password, student_name, parent_name, phone, email, class_grade, school_name, address, avatar)
                    VALUES (:username, :password, :student_name, :parent_name, :phone, :email, :class_grade, :school_name, :address, :avatar)
                ''', user_dict)
                conn.commit()
        except sqlite3.IntegrityError:
            # Fallback if username already exists
            pass
            
        session['user'] = user_dict
        return redirect(url_for('index'))
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
SENDER_EMAIL = "namanhometutors@gmail.com" # Updated automatically!
SENDER_PASSWORD = "vbwhkleylfrswrvv "  # Removed the spaces for standard API compliance
RECEIVER_EMAIL = "namanhometutors@gmail.com"

@app.route('/submit-application', methods=['POST'])
def submit_application():
    """Handles CV upload and sends an ACTUAL email via Gmail SMTP."""
    name = request.form.get('name')
    phone = request.form.get('phone')
    cv_file = request.files.get('cv_file')
    
    if cv_file and cv_file.filename != '':
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
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    message = request.form.get('message')
    
    if not name or not message:
        return "Invalid form.", 400

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
    
    try:
        if SENDER_EMAIL != "your-email@gmail.com":
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
                smtp.send_message(msg)
            print("📧 CONTACT EMAIL SENT SUCCESSFULLY!")
        else:
            print("⚠️ APP PASSWORD NOT CONFIGURED YET! Email skipped.")
    except Exception as e:
        print(f"FAILED TO SEND EMAIL: {str(e)}")
        
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

if __name__ == '__main__':
    # Run Flask Application on port 5000 in local debug mode
    app.run(debug=True, port=5000)
