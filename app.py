from flask import Flask, render_template, request, redirect,flash, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "hospital_secret"

# ------------------ DATABASE ------------------

def get_db():
    conn = sqlite3.connect("hospital.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT UNIQUE,
                    password TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT UNIQUE,
                    password TEXT,
                    specialization TEXT,
                    cabin TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER,
                    doctor_id INTEGER,
                    date TEXT,
                    prescription TEXT,
                    status TEXT DEFAULT 'Pending'
                )''')

    conn.commit()
    conn.close()

init_db()

# ------------------ HOME ------------------

@app.route('/')
def index():
    return render_template("index.html")

# ------------------ REGISTRATION ------------------

@app.route('/register_patient', methods=['GET', 'POST'])
def register_patient():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        try:
            conn.execute("INSERT INTO patients (name,email,password) VALUES (?,?,?)",
                         (name,email,password))
            conn.commit()
        except:
            return "Email already exists!"
        conn.close()
        return redirect('/login')

    return render_template("register_patient.html")


@app.route('/register_doctor', methods=['GET', 'POST'])
def register_doctor():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        specialization = request.form['specialization']
        cabin = request.form['cabin']

        conn = get_db()
        try:
            conn.execute("INSERT INTO doctors (name,email,password,specialization,cabin) VALUES (?,?,?,?,?)",
                         (name,email,password,specialization,cabin))
            conn.commit()
        except:
            return "Email already exists!"
        conn.close()
        return redirect('/login')

    return render_template("register_doctor.html")

# ------------------ LOGIN ------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        conn = get_db()

        if role == "patient":
            user = conn.execute("SELECT * FROM patients WHERE email=? AND password=?",
                                (email,password)).fetchone()
            if user:
                session['user_id'] = user['id']
                session['role'] = "patient"
                return redirect('/patient_dashboard')

        if role == "doctor":
            user = conn.execute("SELECT * FROM doctors WHERE email=? AND password=?",
                                (email,password)).fetchone()
            if user:
                session['user_id'] = user['id']
                session['role'] = "doctor"
                return redirect('/doctor_dashboard')

        return "Invalid Credentials!"

    return render_template("login.html")

# ------------------ PATIENT DASHBOARD ------------------

@app.route('/patient_dashboard')
def patient_dashboard():
    if session.get('role') != 'patient':
        return redirect('/login')

    conn = get_db()
    doctors = conn.execute("SELECT * FROM doctors").fetchall()
    conn.close()

    return render_template("patient_dashboard.html", doctors=doctors)
# ------------------ BOOK APPOINTMENT ------------------

@app.route('/book/<int:doctor_id>', methods=['POST'])
def book(doctor_id):
    date = request.form['date']

    conn = get_db()
    conn.execute(
        "INSERT INTO appointments (patient_id, doctor_id, date) VALUES (?, ?, ?)",
        (session['user_id'], doctor_id, date)
    )
    conn.commit()
    conn.close()

    flash("Appointment request sent successfully!")
    return redirect('/patient_dashboard')
# ------------------ DOCTOR DASHBOARD ------------------

@app.route('/doctor_dashboard')
def doctor_dashboard():
    conn = get_db()
    appointments = conn.execute("""
        SELECT appointments.id,
               patients.name,
               appointments.date,
               appointments.status,
               appointments.prescription
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.id
        WHERE appointments.doctor_id = ?
    """, (session['user_id'],)).fetchall()
    conn.close()

    return render_template("doctor_dashboard.html", appointments=appointments)
# ------------------ UPDATE STATUS ------------------

@app.route('/update/<int:id>/<status>')
def update(id, status):
    conn = get_db()
    conn.execute("UPDATE appointments SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    return redirect('/doctor_dashboard')
@app.route('/patient_appointments')
def patient_appointments():
    conn = get_db()
    appointments = conn.execute("""
        SELECT appointments.id,
               doctors.name,
               appointments.date,
               appointments.status,
               appointments.prescription
        FROM appointments
        JOIN doctors ON appointments.doctor_id = doctors.id
        WHERE appointments.patient_id = ?
    """, (session['user_id'],)).fetchall()
    conn.close()

    return render_template("patient_appointments.html", appointments=appointments)
@app.route('/add_prescription/<int:appointment_id>', methods=['GET', 'POST'])
def add_prescription(appointment_id):

    conn = get_db()

    if request.method == 'POST':
        prescription = request.form['prescription']

        conn.execute("""
            UPDATE appointments
            SET prescription = ?
            WHERE id = ?
        """, (prescription, appointment_id))

        conn.commit()
        conn.close()

        return redirect('/doctor_dashboard')

    appointment = conn.execute("""
        SELECT prescription
        FROM appointments
        WHERE id = ?
    """, (appointment_id,)).fetchone()

    conn.close()

    return render_template("add_prescription.html", appointment=appointment)
@app.route('/view_prescription/<int:appointment_id>')
def view_prescription(appointment_id):

    if session.get('role') != 'patient':
        return redirect('/login')

    conn = get_db()
    appointment = conn.execute("""
        SELECT doctors.name,
               appointments.date,
               appointments.prescription
        FROM appointments
        JOIN doctors ON appointments.doctor_id = doctors.id
        WHERE appointments.id = ?
        AND appointments.patient_id = ?
    """, (appointment_id, session['user_id'])).fetchone()
    conn.close()

    if not appointment:
        return "Unauthorized Access"

    return render_template("view_prescription.html", appointment=appointment)
# ------------------ LOGOUT ------------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)