from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key_crime_system'

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'newpassword',
    'database': 'crime_management'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

# Helpers
def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first.", "danger")
            return redirect(url_for('login'))
    wrap.__name__ = f.__name__
    return wrap

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return render_template('register.html')
            
        cursor = conn.cursor(dictionary=True)
        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash("Username already exists. Please choose a different one.", "danger")
        else:
            # Insert the new user into SQL
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
            conn.commit()
            flash("Account created successfully! You can now login.", "success")
            cursor.close()
            conn.close()
            return redirect(url_for('login'))
            
        cursor.close()
        conn.close()
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return render_template('login.html')
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s AND role = %s", (username, password, role))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials. Please try again.", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    stats = {}
    cursor.execute("SELECT COUNT(*) as count FROM crime_reports")
    stats['total_crimes'] = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM criminal_records")
    stats['total_criminals'] = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM case_assignments")
    stats['total_cases'] = cursor.fetchone()['count']
    
    cursor.execute("SELECT * FROM crime_reports ORDER BY date_reported DESC LIMIT 5")
    recent_reports = cursor.fetchall()

    # Cases Sorting / Filtering
    sort_date = request.args.get('sort_date', 'DESC')
    filter_status = request.args.get('status', 'All')
    
    query = """
    SELECT c.*, u.username as officer_name 
    FROM case_assignments c 
    LEFT JOIN users u ON c.assigned_officer_id = u.id
    """
    params = []
    
    if filter_status != 'All':
        query += " WHERE c.status = %s"
        params.append(filter_status)
        
    if sort_date == 'ASC':
        query += " ORDER BY c.date_assigned ASC"
    else:
        query += " ORDER BY c.date_assigned DESC"
        
    cursor.execute(query, tuple(params))
    filtered_cases = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', stats=stats, recent_reports=recent_reports, cases=filtered_cases, sort_date=sort_date, filter_status=filter_status)

@app.route('/crime_reports', methods=['GET', 'POST'])
@login_required
def crime_reports():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST' and session.get('role') == 'Police':
        # Add new report
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        
        cursor.execute("INSERT INTO crime_reports (title, description, location) VALUES (%s, %s, %s)", 
                       (title, description, location))
        conn.commit()
        flash("Crime report added successfully.", "success")
        return redirect(url_for('crime_reports'))
        
    cursor.execute("SELECT * FROM crime_reports ORDER BY date_reported DESC")
    reports = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('crime_reports.html', reports=reports)

@app.route('/delete_crime/<int:id>', methods=['POST'])
@login_required
def delete_crime(id):
    if session.get('role') != 'Police':
        abort(403)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM crime_reports WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Report deleted.", "success")
    return redirect(url_for('crime_reports'))

@app.route('/criminal_records', methods=['GET', 'POST'])
@login_required
def criminal_records():
    if request.method == 'POST' and session.get('role') != 'Police':
        abort(403)
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        crime = request.form.get('crime_committed')
        arrest_date = request.form.get('arrest_date')
        
        cursor.execute("""
            INSERT INTO criminal_records (name, age, gender, crime_committed, arrest_date) 
            VALUES (%s, %s, %s, %s, %s)""", 
            (name, age, gender, crime, arrest_date)
        )
        conn.commit()
        flash("Criminal record added.", "success")
        return redirect(url_for('criminal_records'))
        
    cursor.execute("SELECT * FROM criminal_records ORDER BY id DESC")
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('criminal_records.html', records=records)

@app.route('/delete_criminal/<int:id>', methods=['POST'])
@login_required
def delete_criminal(id):
    if session.get('role') != 'Police':
        abort(403)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM criminal_records WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Criminal record deleted.", "success")
    return redirect(url_for('criminal_records'))

@app.route('/case_assignments', methods=['GET', 'POST'])
@login_required
def case_assignments():
    if request.method == 'POST' and session.get('role') != 'Police':
        abort(403)
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            case_name = request.form.get('case_name')
            officer_id = request.form.get('assigned_officer_id')
            status = request.form.get('status')
            date_assigned = request.form.get('date_assigned')
            duration = request.form.get('duration_days')
            
            cursor.execute("""
                INSERT INTO case_assignments (case_name, assigned_officer_id, status, date_assigned, duration_days)
                VALUES (%s, %s, %s, %s, %s)""",
                (case_name, officer_id, status, date_assigned, duration)
            )
            flash("Case assigned successfully.", "success")
            
        elif action == 'edit':
            case_id = request.form.get('case_id')
            status = request.form.get('status')
            duration = request.form.get('duration_days')
            
            cursor.execute("UPDATE case_assignments SET status=%s, duration_days=%s WHERE id=%s", (status, duration, case_id))
            flash("Case updated successfully.", "success")
            
        conn.commit()
        return redirect(url_for('case_assignments'))
        
    # Fetch cases
    query = """
    SELECT c.*, u.username as officer_name 
    FROM case_assignments c 
    LEFT JOIN users u ON c.assigned_officer_id = u.id
    ORDER BY c.date_assigned DESC
    """
    cursor.execute(query)
    cases = cursor.fetchall()
    
    # Fetch officers for the dropdown
    cursor.execute("SELECT id, username FROM users WHERE role='Police'")
    officers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('case_assignments.html', cases=cases, officers=officers)

@app.route('/delete_case/<int:id>', methods=['POST'])
@login_required
def delete_case(id):
    if session.get('role') != 'Police':
        abort(403)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM case_assignments WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Case deleted.", "success")
    return redirect(url_for('case_assignments'))

@app.route('/api/crime/<int:id>')
@login_required
def api_get_crime(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM crime_reports WHERE id = %s", (id,))
    crime = cursor.fetchone()
    cursor.close()
    conn.close()
    if crime:
        if crime.get('date_reported'):
            crime['date_reported'] = crime['date_reported'].strftime('%Y-%m-%d %H:%M')
        return jsonify(crime)
    return jsonify({"error": "Not found"}), 404

@app.route('/api/criminal/<int:id>')
@login_required
def api_get_criminal(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM criminal_records WHERE id = %s", (id,))
    criminal = cursor.fetchone()
    cursor.close()
    conn.close()
    if criminal:
        if hasattr(criminal.get('arrest_date'), 'strftime'):
            criminal['arrest_date'] = criminal['arrest_date'].strftime('%Y-%m-%d')
        return jsonify(criminal)
    return jsonify({"error": "Not found"}), 404

@app.route('/api/police/<int:id>')
@login_required
def api_get_police(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username as name, post, specialization FROM users WHERE id = %s AND role = 'Police'", (id,))
    police = cursor.fetchone()
    cursor.close()
    conn.close()
    if police:
        return jsonify(police)
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
