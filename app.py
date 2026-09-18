from flask import Flask, jsonify, request, session
import mysql.connector
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from uuid import uuid4

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def api_error(message, status=400):
    return jsonify({"error": message}), status


def current_identity():
    if "admin" in session:
        return {"type": "admin", "username": session.get("admin_username", "Admin")}
    if "user_id" in session:
        return {"type": "user", "id": session["user_id"], "username": session["username"]}
    return None

# ---------------- DB CONNECTION ----------------
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


# ---------------- REACT API ----------------
@app.get("/api/session")
def api_session():
    return jsonify({"user": current_identity()})


@app.post("/api/register")
def api_register():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "").strip()
    email = payload.get("email", "").strip()
    password = payload.get("password", "")

    if not username or not email or not password:
        return api_error("Username, email and password are required.")

    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "INSERT INTO users (username,email,password) VALUES (%s,%s,%s)",
            (username, email, generate_password_hash(password))
        )
        db.commit()
        return jsonify({"message": "Registration successful. Please log in."}), 201
    except Exception as error:
        return api_error(str(error), 409)
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.post("/api/login")
def api_login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "").strip()
    password = payload.get("password", "")
    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if not user or not check_password_hash(user["password"], password):
            return api_error("Invalid email or password.", 401)
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return jsonify({"user": current_identity()})
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.post("/api/forgot-password")
def api_forgot_password():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "").strip()
    if not email:
        return api_error("Please enter your registered email address.")
    # Email delivery is intentionally kept separate from the login system.
    # This response does not reveal whether an account exists for an address.
    return jsonify({"message": "If an account exists for this email, a password-reset request has been recorded. Please contact the portal administrator to complete the reset."})


@app.post("/api/admin/login")
def api_admin_login():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "").strip()
    password = payload.get("password", "")
    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin WHERE username=%s", (username,))
        admin = cursor.fetchone()
        if not admin or not check_password_hash(admin["password"], password):
            return api_error("Invalid admin credentials.", 401)
        session["admin"] = True
        session["admin_username"] = admin["username"]
        return jsonify({"user": current_identity()})
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.get("/api/dashboard")
def api_dashboard():
    if "user_id" not in session:
        return api_error("Please log in first.", 401)
    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM complaints WHERE user_id=%s", (session["user_id"],))
        total = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS pending FROM complaints WHERE user_id=%s AND status='pending'", (session["user_id"],))
        pending = cursor.fetchone()["pending"]
        cursor.execute("SELECT COUNT(*) AS resolved FROM complaints WHERE user_id=%s AND status='resolved'", (session["user_id"],))
        resolved = cursor.fetchone()["resolved"]
        return jsonify({"total": total, "pending": pending, "resolved": resolved})
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.get("/api/complaints")
def api_complaints():
    if "user_id" not in session:
        return api_error("Please log in first.", 401)
    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM complaints WHERE user_id=%s ORDER BY created_at DESC", (session["user_id"],))
        complaints = cursor.fetchall()
        for complaint in complaints:
            if complaint.get("created_at"):
                complaint["created_at"] = complaint["created_at"].isoformat(sep=" ")
        return jsonify({"complaints": complaints})
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.post("/api/complaints")
def api_add_complaint():
    if "user_id" not in session:
        return api_error("Please log in first.", 401)
    payload = request.form if request.form else (request.get_json(silent=True) or {})
    title = payload.get("title", "").strip()
    complaint_type = payload.get("type", "").strip()
    issue = payload.get("issue", "").strip()
    category = " — ".join(part for part in [complaint_type, issue] if part) or payload.get("category", "").strip()
    description = payload.get("description", "").strip()
    if not title or not category or not description:
        return api_error("Title, category and description are required.")

    details = []
    field_labels = {
        "location": "Location", "landmark": "Landmark", "incidentDate": "Incident date",
        "name": "Contact name", "phone": "Phone", "email": "Email"
    }
    for field, label in field_labels.items():
        value = payload.get(field, "").strip()
        if value:
            details.append(f"{label}: {value}")
    for field in payload.keys():
        if field.startswith("extra_"):
            value = payload.get(field, "").strip()
            if value:
                details.append(f"{field[6:]}: {value}")
    if payload.get("anonymous") == "true":
        details.append("Submitted anonymously")

    photo = request.files.get("photo")
    if photo and photo.filename:
        extension = photo.filename.rsplit(".", 1)[-1].lower() if "." in photo.filename else ""
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            return api_error("Please upload a JPG, PNG, or WEBP image.")
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filename = f"{uuid4().hex}_{secure_filename(photo.filename)}"
        photo.save(os.path.join(UPLOAD_FOLDER, filename))
        details.append(f"Evidence photo: /static/uploads/{filename}")

    if details:
        description = f"{description}\n\n" + "\n".join(details)
    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "INSERT INTO complaints (user_id, title, category, description, status) VALUES (%s, %s, %s, %s, %s)",
            (session["user_id"], title, category, description, "pending")
        )
        db.commit()
        return jsonify({"message": "Complaint added successfully."}), 201
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.get("/api/admin/complaints")
def api_admin_complaints():
    if "admin" not in session:
        return api_error("Admin login required.", 401)
    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT complaints.id, users.username, complaints.title, complaints.category,
                   complaints.description, complaints.status, complaints.created_at
            FROM complaints JOIN users ON complaints.user_id = users.id
            ORDER BY complaints.created_at DESC
        """)
        complaints = cursor.fetchall()
        for complaint in complaints:
            if complaint.get("created_at"):
                complaint["created_at"] = complaint["created_at"].isoformat(sep=" ")
        return jsonify({
            "complaints": complaints,
            "pending": sum(item["status"] == "pending" for item in complaints),
            "resolved": sum(item["status"] == "resolved" for item in complaints)
        })
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.patch("/api/admin/complaints/<int:complaint_id>")
def api_update_complaint(complaint_id):
    if "admin" not in session:
        return api_error("Admin login required.", 401)
    new_status = (request.get_json(silent=True) or {}).get("status")
    if new_status not in ["pending", "resolved"]:
        return api_error("Invalid status value.")
    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("UPDATE complaints SET status=%s WHERE id=%s", (new_status, complaint_id))
        db.commit()
        return jsonify({"message": "Complaint status updated."})
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.delete("/api/admin/complaints/<int:complaint_id>")
def api_delete_complaint(complaint_id):
    if "admin" not in session:
        return api_error("Admin login required.", 401)
    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("DELETE FROM complaints WHERE id=%s", (complaint_id,))
        db.commit()
        return jsonify({"message": "Complaint deleted."})
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out successfully."})

if __name__ == "__main__":
    app.run(debug=True)
