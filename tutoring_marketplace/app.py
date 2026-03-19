from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'super_secret_naman_key_123'

DATABASE = 'tutors.db'

def init_db():
    """Initializes the SQLite database and seeds default tutors."""
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

@app.route('/login')
def login():
    """Renders the login page."""
    return render_template('login.html')

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template('contact.html')

@app.route('/book-demo', methods=['GET', 'POST'])
def book_demo():
    """Renders the book free demo page and handles registration submission."""
    if request.method == 'POST':
        # The multi-step form simulates a registration signup.
        form_data = request.form.to_dict()
        session['user'] = {
            'username': form_data.get('username'),
            'avatar': form_data.get('avatar', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix'),
            'student_name': form_data.get('student_name'),
            'parent_name': form_data.get('parent_name'),
            'phone': form_data.get('phone'),
            'email': form_data.get('email'),
            'class_grade': form_data.get('class_grade'),
            'school_name': form_data.get('school_name'),
            'address': form_data.get('address')
        }
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

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/submit-application', methods=['POST'])
def submit_application():
    """Handles CV upload and simulates sending an email to the host."""
    name = request.form.get('name')
    phone = request.form.get('phone')
    cv_file = request.files.get('cv_file')
    
    if cv_file and cv_file.filename != '':
        filename = secure_filename(cv_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{name.replace(' ', '_')}_{filename}")
        cv_file.save(file_path)
        
        # --- EMAIL SIMULATOR ---
        # In a real production app, you'd use smtplib or a mail service like SendGrid here.
        print("\n" + "="*60)
        print(" 📧 NEW EMAIL SENT TO HOST: admin@namantutors.com")
        print("="*60)
        print(f"Subject: New Tutor Application - {name}")
        print(f"Applicant Name : {name}")
        print(f"Contact Number : {phone}")
        print(f"CV Attachment  : Successfully attached ({file_path})")
        print("Note: All details (salary, experience) are inside the CV.")
        print("="*60 + "\n")
        
        return '''
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <body style="background:#f9fafb; font-family:sans-serif;"></body>
        <script>
            Swal.fire({
                title: 'Application Sent to Host!',
                text: 'Your CV and details have been emailed successfully. We will review it shortly!',
                icon: 'success',
                confirmButtonColor: '#111827',
                confirmButtonText: 'Return Home'
            }).then(() => {
                window.location.href = "/";
            });
        </script>
        '''
    return "Invalid File Upload.", 400

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
    # Initialize the DB first implicitly before running the app
    init_db()
    # Run Flask Application on port 5000 in debug mode
    app.run(debug=True, port=5000)
