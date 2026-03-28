from flask import Flask, render_template, request, session, redirect, jsonify
import sqlite3, hashlib

app = Flask(__name__)
app.secret_key = "edulite_secret_key_2024"

def get_db():
    conn = sqlite3.connect("edulite.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    # Existing tables...
    db.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        grade TEXT NOT NULL,
        language TEXT DEFAULT 'english',
        password TEXT NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject TEXT,
        score INTEGER,
        total INTEGER,
        date TEXT DEFAULT CURRENT_DATE
    )""")
    # ADD THIS NEW TABLE
    db.execute("""CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        role TEXT,
        message TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    db.commit()
    db.close()

# ADD THIS NEW ROUTE to fetch history for the UI
@app.route("/get_history")
def get_history():
    if "student_id" not in session:
        return jsonify([])
    db = get_db()
    history = db.execute("SELECT role, message FROM chat_history WHERE student_id=? ORDER BY timestamp ASC", 
                         (session["student_id"],)).fetchall()
    db.close()
    return jsonify([dict(row) for row in history])

# ADD THIS NEW ROUTE to save new messages
@app.route("/save_chat", methods=["POST"])
def save_chat():
    data = request.json
    db = get_db()
    db.execute("INSERT INTO chat_history (student_id, role, message) VALUES (?,?,?)",
               (session["student_id"], data["role"], data["message"]))
    db.commit()
    db.close()
    return jsonify({"status": "saved"})

@app.route("/")
def index():
    if "student_id" in session:
        return redirect("/dashboard")
    return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    grade = request.form["grade"]
    language = request.form.get("language", "english")
    password = hashlib.sha256(request.form["password"].encode()).hexdigest()
    db = get_db()
    try:
        db.execute("INSERT INTO students (name, grade, language, password) VALUES (?,?,?,?)",
                   (name, grade, language, password))
        db.commit()
    except:
        return render_template("login.html", error="Name already taken")
    finally:
        db.close()
    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    name = request.form["name"]
    password = hashlib.sha256(request.form["password"].encode()).hexdigest()
    db = get_db()
    student = db.execute("SELECT * FROM students WHERE name=? AND password=?",
                         (name, password)).fetchone()
    db.close()
    if student:
        session["student_id"] = student["id"]
        session["name"] = student["name"]
        session["grade"] = student["grade"]
        session["language"] = student["language"]
        return redirect("/dashboard")
    return render_template("login.html", error="Wrong name or password")

@app.route("/dashboard")
def dashboard():
    if "student_id" not in session:
        return redirect("/")
    return render_template("dashboard.html", name=session["name"], grade=session["grade"])

@app.route("/chat")
def chat():
    if "student_id" not in session:
        return redirect("/")
    return render_template("chat.html", name=session["name"],
                           grade=session["grade"], language=session.get("language","english"))

@app.route("/quiz")
def quiz():
    if "student_id" not in session:
        return redirect("/")
    return render_template("quiz.html", grade=session["grade"])

@app.route("/save_score", methods=["POST"])
def save_score():
    if "student_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.json
    db = get_db()
    db.execute("INSERT INTO progress (student_id, subject, score, total) VALUES (?,?,?,?)",
               (session["student_id"], data["subject"], data["score"], data.get("total", 5)))
    db.commit()
    db.close()
    return jsonify({"status": "saved"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    print("Starting EduLite Web App on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)
