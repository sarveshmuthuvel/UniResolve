"""
database.py - Everything that talks to the SQLite database lives here.

The UI (app.py) never writes SQL itself. It only calls these functions,
which keeps the screens simple and the data logic in one place.
"""

import hashlib
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "uniresolve.db")
SCHEMA_FILE = os.path.join(BASE_DIR, "schema.sql")

CATEGORIES = ["Infrastructure", "Electrical", "IT & Network", "Cleanliness", "Classroom & Lab"]
LOCATIONS = ["Tech Park 1", "Tech Park 2", "Java Canteen", "University Building", "TP Ganesan", "Vendhar Square", "Hostel"]
PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Pending", "In Progress", "Resolved"]


def connect():
    """Open a connection. row_factory lets us read columns by name: row['title']."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def ticket_id(complaint_id):
    """Turn database id 7 into a friendly ticket number CMP007."""
    return f"CMP{complaint_id:03d}"


# ---------------------------------------------------------------- setup

def init_db():
    """Create the tables (if missing) and add demo data on the very first run."""
    with connect() as conn:
        with open(SCHEMA_FILE) as f:
            conn.executescript(f.read())
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            _seed(conn)


def _seed(conn):
    users = [
        ("admin", "admin123", "Admin", "admin", None, "admin@srmist.edu.in", "Facility Management"),
        ("student1", "student123", "Rahul Sharma", "student", "RA2511003010001", "rahul.sharma@srmist.edu.in", "CSE"),
        ("student2", "student123", "Priya Patel", "student", "RA2511003010045", "priya.patel@srmist.edu.in", "ECE"),
    ]
    for u in users:
        conn.execute(
            "INSERT INTO users (username, password, name, role, reg_no, email, department) VALUES (?,?,?,?,?,?,?)",
            (u[0], hash_password(u[1]), *u[2:]),
        )

    complaints = [
        # user_id, title, category, location, priority, description, status, remarks, created_at
        (2, "Projector not working in Room 402", "Classroom & Lab", "Tech Park 1", "High",
         "The projector shows 'No Signal' with every laptop. Lectures are getting delayed.",
         "In Progress", "Technician assigned. Replacement HDMI cable ordered.", "2026-11-10 09:15:00"),
        (2, "Wi-Fi drops every few minutes", "IT & Network", "University Building", "Medium",
         "Campus Wi-Fi disconnects frequently on the 3rd floor near the library.",
         "Pending", "", "2026-11-12 14:40:00"),
        (2, "Water leakage near stairs", "Infrastructure", "Tech Park 2", "Medium",
         "Water is leaking from the ceiling near the east staircase. Floor is slippery.",
         "Resolved", "Pipe joint repaired and area cleaned.", "2026-11-05 11:05:00"),
        (3, "Tables not cleaned during lunch", "Cleanliness", "Java Canteen", "Low",
         "Tables stay dirty for a long time during peak lunch hours.",
         "Pending", "", "2026-11-13 13:20:00"),
        (3, "Fan making loud noise", "Electrical", "Hostel", "Low",
         "Ceiling fan in room B-214 makes a grinding noise at high speed.",
         "Resolved", "Fan bearing replaced.", "2026-11-08 20:10:00"),
        (3, "Lab PCs not booting", "IT & Network", "Tech Park 2", "High",
         "Six systems in Lab 1105 are stuck on the boot screen. We have a lab exam on Friday.",
         "In Progress", "Re-imaging the systems. Expected to finish by Thursday.", "2026-11-14 10:30:00"),
        (2, "Street light broken near gate 3", "Electrical", "Vendhar Square", "Medium",
         "The street light near gate 3 has been off for a week. The path is very dark at night.",
         "Pending", "", "2026-11-15 19:45:00"),
        (3, "Broken bench in auditorium", "Infrastructure", "TP Ganesan", "Low",
         "Two seats in row F of the auditorium are broken and the screws are sticking out.",
         "Pending", "", "2026-11-16 09:05:00"),
    ]
    for c in complaints:
        conn.execute(
            """INSERT INTO complaints
               (user_id, title, category, location, priority, description, status, remarks, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (*c, c[-1]),
        )


# ---------------------------------------------------------------- users

def login(username, password):
    """Return the user row if the username + password match, else None."""
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, hash_password(password)),
        ).fetchone()


def register_student(username, password, name, reg_no, email, department):
    """Create a student account. Returns (ok, message)."""
    try:
        with connect() as conn:
            conn.execute(
                """INSERT INTO users (username, password, name, role, reg_no, email, department)
                   VALUES (?, ?, ?, 'student', ?, ?, ?)""",
                (username, hash_password(password), name, reg_no, email, department),
            )
        return True, "Account created. You can sign in now."
    except sqlite3.IntegrityError:          # UNIQUE constraint on username
        return False, "That username is already taken."


# ---------------------------------------------------------------- complaints

def add_complaint(user_id, title, category, location, priority, description):
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO complaints (user_id, title, category, location, priority, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, title, category, location, priority, description),
        )
        return cur.lastrowid


def get_complaints(user_id=None, status=None, search=""):
    """
    Students pass their user_id to see only their own complaints.
    The admin passes nothing and sees everyone's.
    A JOIN brings in the student's name for each complaint.
    """
    sql = """SELECT c.*, u.name AS student_name, u.reg_no
             FROM complaints c JOIN users u ON u.id = c.user_id
             WHERE 1 = 1"""
    params = []
    if user_id is not None:
        sql += " AND c.user_id = ?"
        params.append(user_id)
    if status and status != "All":
        sql += " AND c.status = ?"
        params.append(status)
    if search:
        sql += " AND (c.title LIKE ? OR c.location LIKE ? OR c.category LIKE ?)"
        params += [f"%{search}%"] * 3
    sql += " ORDER BY c.created_at DESC"
    with connect() as conn:
        return conn.execute(sql, params).fetchall()


def update_status(complaint_id, status, remarks):
    with connect() as conn:
        conn.execute(
            """UPDATE complaints
               SET status = ?, remarks = ?, updated_at = datetime('now', 'localtime')
               WHERE id = ?""",
            (status, remarks, complaint_id),
        )


def delete_complaint(complaint_id):
    """Admin only. The WHERE clause also checks the status, so an open complaint can never be deleted."""
    with connect() as conn:
        cur = conn.execute("DELETE FROM complaints WHERE id = ? AND status = 'Resolved'", (complaint_id,))
        return cur.rowcount == 1


def get_stats(user_id=None):
    """Count complaints per status using GROUP BY. Returns a dict like {'Pending': 2, ...}."""
    sql = "SELECT status, COUNT(*) AS n FROM complaints"
    params = []
    if user_id is not None:
        sql += " WHERE user_id = ?"
        params.append(user_id)
    sql += " GROUP BY status"
    with connect() as conn:
        counts = {row["status"]: row["n"] for row in conn.execute(sql, params)}
    stats = {s: counts.get(s, 0) for s in STATUSES}
    stats["Total"] = sum(stats.values())
    return stats


def get_category_counts():
    with connect() as conn:
        rows = conn.execute(
            "SELECT category, COUNT(*) AS n FROM complaints GROUP BY category ORDER BY n DESC"
        ).fetchall()
    return [(r["category"], r["n"]) for r in rows]
