from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3

print("THIS IS THE CORRECT APP FILE RUNNING")

app = Flask(__name__)
app.secret_key = "techcare_secret_key"

# -------------------------------
# Database Connection
# -------------------------------
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------------
# Initialize Database
# -------------------------------
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS booking (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        device TEXT NOT NULL,
        issue TEXT NOT NULL,
        service_method TEXT NOT NULL,
        status TEXT DEFAULT 'Pending'
    )
    ''')

    conn.commit()
    conn.close()

# -------------------------------
# Routes
# -------------------------------

# Home route
@app.route('/')
def home():
    return "TechCare Backend Running"

# Debug route
@app.route('/check')
def check():
    return "Check route working"

# Registration page (HTML)
@app.route('/register-page')
def register_page():
    return render_template('register.html')

# Registration API
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')

    # -------------------------------
    # Validation
    # -------------------------------
    if not name or not email or not phone or not password:
        return jsonify({"error": "All fields are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO user (name, email, phone, password) VALUES (?, ?, ?, ?)",
            (name, email, phone, password)
        )
        conn.commit()

        return jsonify({
            "message": "User registered successfully",
            "redirect": "/login-page"
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400

# Login page (HTML)
@app.route('/login-page')
def login_page():
    return render_template('login.html')

# Login API
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    #ADMIN LOGIN
    if email == "admin@techcare.com" and password == "admin123":
        session['admin'] = True
        return jsonify({"message": "Admin login successful", "redirect": "/admin"})

    #NORMAL USER LOGIN
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM user WHERE email=? AND password=?",
        (email, password)
    ).fetchone()

    if user:
        session['user'] = email
        return jsonify({"message": "Login successful", "redirect": "/home"})
    else:
        return jsonify({"error": "Invalid email or password"}), 401
    
# Booking page (HTML)
@app.route('/booking-page')
def booking_page():
    if 'user' not in session and 'admin' not in session:
            return redirect('/login-page')  # redirect if not logged in
    return render_template('booking.html')

# Booking API
@app.route('/booking', methods=['POST'])
def booking():
    data = request.get_json()

    device = data.get('device')
    issue = data.get('issue')
    method = data.get('method')

    if not device or not issue or not method:
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO booking (device, issue, service_method) VALUES (?, ?, ?)",
        (device, issue, method)
    )
    conn.commit()

    return jsonify({
        "message": "Booking submitted successfully",
        "notification": "Your repair request has been received."
    })

# Tracking page (HTML)
@app.route('/track')
def track():
    if 'user' not in session and 'admin' not in session:
        return redirect('/login-page')  # redirect if not logged in
    return render_template('track.html')

#Get Tracking API
@app.route('/get-bookings')
def get_bookings():
    conn = get_db()
    bookings = conn.execute("SELECT * FROM booking").fetchall()

    result = []
    for b in bookings:
        result.append({
            "id": b["booking_id"],
            "device": b["device"],
            "issue": b["issue"],
            "method": b["service_method"],
            "status": b["status"]
        })

    return jsonify(result)

#Update Status
@app.route('/update-status', methods=['POST'])
def update_status():
    data = request.get_json()

    booking_id = data.get('id')
    status = data.get('status')

    conn = get_db()
    conn.execute(
        "UPDATE booking SET status=? WHERE booking_id=?",
        (status, booking_id)
    )
    conn.commit()

    return jsonify({
        "message": "Status updated successfully",
        "notification": f"Booking status updated to {status}"
    })

#Admin
@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect('/login-page')
    return render_template('admin.html')

# Home page (HTML)
@app.route('/home')
def home_page():
    if 'user' not in session and 'admin' not in session:
        return redirect('/login-page')  # redirect if not logged in
    return render_template('home.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)  #remove session
    session.pop('admin', None) #remove session
    return redirect('/login-page')

# -------------------------------
# Run App
# -------------------------------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)