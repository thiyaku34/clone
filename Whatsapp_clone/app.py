from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow cross-origin

# -------------------------------
# Database helper
# -------------------------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------------
# Routes
# -------------------------------
from flask import jsonify

@app.route("/add_contact", methods=["POST"])
def add_contact():
    if "username" not in session:
        return jsonify({"status":"error","msg":"Login required"})
    new_user = request.form.get("username").strip()
    if not new_user:
        return jsonify({"status":"error","msg":"Empty username"})
    db = get_db()
    try:
        db.execute("INSERT INTO users (username,password) VALUES (?,?)", (new_user,"1234"))
        db.commit()
        return jsonify({"status":"success","username":new_user})
    except sqlite3.IntegrityError:
        return jsonify({"status":"error","msg":"User already exists"})

@app.route("/delete_contact", methods=["POST"])
def delete_contact():
    if "username" not in session:
        return jsonify({"status":"error","msg":"Login required"})
    user_to_delete = request.form.get("username").strip()
    db = get_db()
    db.execute("DELETE FROM users WHERE username=?", (user_to_delete,))
    db.commit()
    return jsonify({"status":"success","username":user_to_delete})

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method=="POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=? AND password=?",
                          (username,password)).fetchone()
        if user:
            session["username"] = username
            return redirect("/home")
        return "Login Failed"
    return render_template("login.html")

@app.route("/home")
def home():
    if "username" not in session:
        return redirect("/")
    db = get_db()
    users = db.execute("SELECT username FROM users WHERE username != ?",
                       (session["username"],)).fetchall()
    return render_template("home.html", users=users)

@app.route("/chat/<user>")
def chat(user):
    if "username" not in session:
        return redirect("/")
    return render_template("chat.html", user=user, me=session["username"])

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")

# -------------------------------
# Socket.IO Events
# -------------------------------

# Text messages
@socketio.on("message")
def handle_message(data):
    """
    data = { user: sender, to: receiver, message: text }
    """
    db = get_db()
    db.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
               (data["user"], data["to"], data["message"]))
    db.commit()
    emit("new_message", data, broadcast=True)

# Image messages
@socketio.on("image")
def handle_image(data):
    emit("new_image", data, broadcast=True)

# Typing indicator
@socketio.on("typing")
def handle_typing(data):
    emit("typing", data, broadcast=True)

# -------------------------------
# WebRTC Signaling for Voice/Video
# -------------------------------
@socketio.on("call_offer")
def call_offer(data):
    emit("call_offer", data, broadcast=True)

@socketio.on("call_answer")
def call_answer(data):
    emit("call_answer", data, broadcast=True)

@socketio.on("ice_candidate")
def ice_candidate(data):
    emit("ice_candidate", data, broadcast=True)

# -------------------------------
# Run server
# -------------------------------
if __name__=="__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)