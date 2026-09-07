"""
Job Portal — a Flask web app where users sign up, log in, upload their resume,
and instantly see jobs (aggregated from multiple mock platforms: LinkedIn,
Indeed, Naukri, Glassdoor, Monster) ranked by how well they match the user's
extracted skills.

Run with:
    pip install flask pdfplumber python-docx
    python app.py
Then open http://127.0.0.1:5000
"""
import os
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import db
from utils.resume_parser import parse_resume, MASTER_SKILLS
from utils.job_matcher import load_jobs, match_jobs, get_platforms

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max resume size

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
db.init_db()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapped


def current_user():
    if "user_id" not in session:
        return None
    return db.get_user_by_id(session["user_id"])


def skills_csv_to_list(skills_csv):
    if not skills_csv:
        return []
    return [s.strip() for s in skills_csv.split(",") if s.strip()]


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html")

        if db.get_user_by_email(email):
            flash("An account with that email already exists. Please log in.", "danger")
            return redirect(url_for("login"))

        password_hash = generate_password_hash(password)
        user_id = db.create_user(name, email, password_hash)
        session["user_id"] = user_id
        flash("Account created! Now upload your resume to get matched to jobs.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        session["user_id"] = user["id"]
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard / resume upload
# ---------------------------------------------------------------------------
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    user = current_user()

    if request.method == "POST":
        file = request.files.get("resume")
        if not file or file.filename == "":
            flash("Please choose a resume file to upload.", "danger")
            return redirect(url_for("dashboard"))

        if not allowed_file(file.filename):
            flash("Unsupported file type. Please upload a PDF, DOCX, or TXT file.", "danger")
            return redirect(url_for("dashboard"))

        filename = secure_filename(f"user_{user['id']}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        try:
            _, skills_found = parse_resume(filepath)
        except Exception as exc:  # noqa: BLE001
            flash(f"Could not read that resume file: {exc}", "danger")
            return redirect(url_for("dashboard"))

        db.update_resume(user["id"], filename, ",".join(skills_found))

        if skills_found:
            flash(
                f"Resume uploaded! Detected {len(skills_found)} skill(s). "
                "Review them below and head to 'Matched Jobs'.",
                "success",
            )
        else:
            flash(
                "Resume uploaded, but no known skills were detected automatically. "
                "Add your skills manually below.",
                "warning",
            )
        return redirect(url_for("dashboard"))

    user = current_user()
    user_skills = skills_csv_to_list(user["skills"])
    return render_template(
        "dashboard.html",
        user=user,
        user_skills=user_skills,
        all_skills=MASTER_SKILLS,
    )


@app.route("/skills/update", methods=["POST"])
@login_required
def update_skills():
    selected = request.form.getlist("skills")
    manual = request.form.get("manual_skills", "")
    manual_list = [s.strip().lower() for s in manual.split(",") if s.strip()]
    combined = sorted(set([s.lower() for s in selected] + manual_list))
    db.update_skills(session["user_id"], ",".join(combined))
    flash("Your skills profile has been updated.", "success")
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------------------
# Job matching
# ---------------------------------------------------------------------------
@app.route("/jobs")
@login_required
def jobs():
    user = current_user()
    user_skills = skills_csv_to_list(user["skills"])

    platform_filter = request.args.get("platform") or None
    all_jobs = load_jobs()
    platforms = get_platforms(all_jobs)

    if not user_skills:
        flash("Add skills to your profile first so we can match you to jobs.", "warning")
        return redirect(url_for("dashboard"))

    matched = match_jobs(user_skills, all_jobs, min_score=1, platform=platform_filter)

    return render_template(
        "jobs.html",
        user=user,
        user_skills=user_skills,
        matched_jobs=matched,
        platforms=platforms,
        active_platform=platform_filter,
    )


if __name__ == "__main__":
    app.run(debug=True)
