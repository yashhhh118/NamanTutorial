from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)

DATABASE = 'tutors.db'

def init_db():
    """Initializes the SQLite database with the required table for lead capture."""
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
        conn.commit()

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
