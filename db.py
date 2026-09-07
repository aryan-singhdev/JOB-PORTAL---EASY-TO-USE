"""
Lightweight SQLite database layer for the Job Portal app.
No ORM is used so the project only depends on Flask + the Python standard library
(plus pdfplumber / python-docx for resume parsing).
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "job_portal.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            resume_filename TEXT,
            skills TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def create_user(name, email, password_hash):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id


def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def update_resume(user_id, resume_filename, skills_csv):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET resume_filename = ?, skills = ? WHERE id = ?",
        (resume_filename, skills_csv, user_id),
    )
    conn.commit()
    conn.close()


def update_skills(user_id, skills_csv):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET skills = ? WHERE id = ?", (skills_csv, user_id))
    conn.commit()
    conn.close()
