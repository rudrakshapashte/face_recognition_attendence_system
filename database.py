import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "attendance.db")


def get_connection():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_database():
    with get_connection() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_no TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Present',
                UNIQUE(student_id, date),
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """)


def add_student(name, roll_no):
    with get_connection() as con:
        cur = con.execute(
            "INSERT INTO students(name, roll_no, created_at) VALUES (?, ?, ?)",
            (name, roll_no, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        return cur.lastrowid


def student_exists(roll_no):
    with get_connection() as con:
        row = con.execute(
            "SELECT id FROM students WHERE roll_no = ?", (roll_no,)
        ).fetchone()
    return row is not None


def get_students():
    with get_connection() as con:
        rows = con.execute(
            "SELECT id, name, roll_no, created_at FROM students ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_student(student_id):
    with get_connection() as con:
        row = con.execute(
            "SELECT id, name, roll_no FROM students WHERE id = ?", (student_id,)
        ).fetchone()
    return dict(row) if row else None


def mark_attendance(student_id):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    with get_connection() as con:
        existing = con.execute(
            "SELECT id FROM attendance WHERE student_id=? AND date=?",
            (student_id, date)
        ).fetchone()

        if existing:
            return False

        con.execute(
            "INSERT INTO attendance(student_id,date,time,status) VALUES(?,?,?,?)",
            (student_id, date, time, "Present")
        )
        return True


def get_attendance(date=None):
    with get_connection() as con:
        if date:
            rows = con.execute("""
                SELECT a.date, a.time, s.name, s.roll_no, a.status
                FROM attendance a
                JOIN students s ON s.id = a.student_id
                WHERE a.date = ?
                ORDER BY a.time DESC
            """, (date,)).fetchall()
        else:
            rows = con.execute("""
                SELECT a.date, a.time, s.name, s.roll_no, a.status
                FROM attendance a
                JOIN students s ON s.id = a.student_id
                ORDER BY a.date DESC, a.time DESC
            """).fetchall()

    return [dict(row) for row in rows]


def get_today_stats():
    today = datetime.now().strftime("%Y-%m-%d")

    with get_connection() as con:
        total = con.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        present = con.execute(
            "SELECT COUNT(*) FROM attendance WHERE date=?", (today,)
        ).fetchone()[0]

    absent = max(total - present, 0)
    percentage = round((present / total) * 100, 1) if total else 0

    return {
        "total_students": total,
        "present": present,
        "absent": absent,
        "percentage": percentage,
        "date": today
    }


def delete_student(student_id):
    with get_connection() as con:
        con.execute("DELETE FROM students WHERE id = ?", (student_id,))
