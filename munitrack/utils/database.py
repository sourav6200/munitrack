import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = "munitrack.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id        TEXT PRIMARY KEY,
        name      TEXT NOT NULL,
        email     TEXT UNIQUE NOT NULL,
        password  TEXT NOT NULL,
        role      TEXT NOT NULL,   -- citizen / admin / worker
        dept      TEXT,            -- worker department
        phone     TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS issues (
        id           TEXT PRIMARY KEY,
        title        TEXT NOT NULL,
        description  TEXT,
        category     TEXT,
        priority     TEXT DEFAULT 'medium',
        status       TEXT DEFAULT 'pending',
        citizen_id   TEXT,
        worker_id    TEXT,
        lat          REAL,
        lng          REAL,
        address      TEXT,
        before_image BLOB,
        after_image  BLOB,
        reported_at  TEXT DEFAULT (datetime('now')),
        assigned_at  TEXT,
        resolved_at  TEXT,
        FOREIGN KEY (citizen_id) REFERENCES users(id),
        FOREIGN KEY (worker_id)  REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS timeline (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id  TEXT NOT NULL,
        text      TEXT NOT NULL,
        color     TEXT DEFAULT '#3b82f6',
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (issue_id) REFERENCES issues(id)
    );
    """)

    # Seed demo users if empty
    existing = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing == 0:
        demo_users = [
            ("u_citizen1", "Rahul Verma",   "citizen@muni.gov",  hash_pw("123"), "citizen", None,         "9876543210"),
            ("u_admin1",   "DM Sharma",     "admin@muni.gov",    hash_pw("123"), "admin",   None,         "9111222333"),
            ("u_worker1",  "Rajesh Kumar",  "worker1@muni.gov",  hash_pw("123"), "worker",  "Roads",      "9222333444"),
            ("u_worker2",  "Sunil Yadav",   "worker2@muni.gov",  hash_pw("123"), "worker",  "Water",      "9333444555"),
            ("u_worker3",  "Priya Singh",   "worker3@muni.gov",  hash_pw("123"), "worker",  "Sanitation", "9444555666"),
        ]
        c.executemany(
            "INSERT INTO users (id, name, email, password, role, dept, phone) VALUES (?,?,?,?,?,?,?)",
            demo_users
        )

        # Seed demo issues
        demo_issues = [
            ("ISS-001", "Pothole on MG Road",
             "Large pothole near Patna Junction causing accidents. Multiple vehicles damaged.",
             "Roads", "high", "assigned",
             "u_citizen1", "u_worker1", 25.6149, 85.1376, "MG Road, Patna",
             "2025-03-10 09:30:00", "2025-03-10 11:00:00", None),
            ("ISS-002", "Broken streetlight",
             "Street light not working for 2 weeks near Boring Road crossing.",
             "Electricity", "medium", "pending",
             "u_citizen1", None, 25.6200, 85.1450, "Boring Road, Patna",
             "2025-03-11 14:00:00", None, None),
            ("ISS-003", "Garbage pile not cleared",
             "Community garbage pile untouched for 5 days, spreading disease risk.",
             "Sanitation", "high", "resolved",
             "u_citizen1", "u_worker3", 25.6100, 85.1300, "Kankarbagh, Patna",
             "2025-03-08 08:00:00", "2025-03-08 10:00:00", "2025-03-09 16:00:00"),
            ("ISS-004", "Water pipe leakage",
             "Underground water pipe broken, water wasting on the road for 3 days.",
             "Water", "high", "assigned",
             "u_citizen1", "u_worker2", 25.6050, 85.1200, "Rajendra Nagar, Patna",
             "2025-03-12 07:00:00", "2025-03-12 09:30:00", None),
        ]
        c.executemany("""
            INSERT INTO issues
              (id, title, description, category, priority, status,
               citizen_id, worker_id, lat, lng, address,
               reported_at, assigned_at, resolved_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, demo_issues)

        # Seed timelines
        demo_tl = [
            ("ISS-001", "Issue reported by Rahul Verma",                     "#3b82f6", "2025-03-10 09:30:00"),
            ("ISS-001", "Assigned to Rajesh Kumar (Roads dept.)",             "#a855f7", "2025-03-10 11:00:00"),
            ("ISS-002", "Issue reported by Rahul Verma",                     "#3b82f6", "2025-03-11 14:00:00"),
            ("ISS-003", "Issue reported by Rahul Verma",                     "#3b82f6", "2025-03-08 08:00:00"),
            ("ISS-003", "Assigned to Priya Singh (Sanitation dept.)",        "#a855f7", "2025-03-08 10:00:00"),
            ("ISS-003", "Work completed — after photo uploaded by Priya Singh", "#22c55e", "2025-03-09 16:00:00"),
            ("ISS-004", "Issue reported by Rahul Verma",                     "#3b82f6", "2025-03-12 07:00:00"),
            ("ISS-004", "Assigned to Sunil Yadav (Water dept.)",             "#a855f7", "2025-03-12 09:30:00"),
        ]
        c.executemany(
            "INSERT INTO timeline (issue_id, text, color, created_at) VALUES (?,?,?,?)",
            demo_tl
        )

    conn.commit()
    conn.close()


# ── Issue helpers ─────────────────────────────────────────────────────────────

def email_exists(email):
    conn = get_conn()
    row = conn.execute("SELECT id FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    conn.close()
    return row is not None


def register_user(name, email, password, role, phone, dept=None):
    """
    Create a new user. Returns (True, user_dict) on success or (False, error_msg) on failure.
    Citizens self-register freely. Workers need a dept.
    Admins cannot self-register (must be seeded by DB admin).
    """
    import uuid
    if email_exists(email):
        return False, "An account with this email already exists."
    uid = "u_" + uuid.uuid4().hex[:10]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = get_conn()
        conn.execute(
            "INSERT INTO users (id, name, email, password, role, dept, phone, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (uid, name.strip(), email.strip().lower(), hash_pw(password), role, dept, phone.strip(), now)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        conn.close()
        return True, dict(row)
    except Exception as e:
        return False, str(e)


def next_issue_id():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
    conn.close()
    return f"ISS-{count + 1:03d}"


def create_issue(title, description, category, priority, citizen_id,
                 lat, lng, address, before_image_bytes):
    issue_id = next_issue_id()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    conn.execute("""
        INSERT INTO issues
          (id, title, description, category, priority, status,
           citizen_id, lat, lng, address, before_image, reported_at)
        VALUES (?,?,?,?,?,'pending',?,?,?,?,?,?)
    """, (issue_id, title, description, category, priority,
          citizen_id, lat, lng, address, before_image_bytes, now))
    conn.execute(
        "INSERT INTO timeline (issue_id, text, color, created_at) VALUES (?,?,?,?)",
        (issue_id, f"Issue reported by citizen", "#3b82f6", now)
    )
    conn.commit()
    conn.close()
    return issue_id


def get_issues(filters=None):
    conn = get_conn()
    sql = """
        SELECT i.*, u.name AS citizen_name, w.name AS worker_name
        FROM issues i
        LEFT JOIN users u ON i.citizen_id = u.id
        LEFT JOIN users w ON i.worker_id  = w.id
    """
    params = []
    if filters:
        clauses = []
        if "citizen_id" in filters:
            clauses.append("i.citizen_id = ?"); params.append(filters["citizen_id"])
        if "worker_id" in filters:
            clauses.append("i.worker_id = ?");  params.append(filters["worker_id"])
        if "status" in filters and filters["status"] != "All":
            clauses.append("i.status = ?");     params.append(filters["status"].lower())
        if "category" in filters and filters["category"] != "All":
            clauses.append("i.category = ?");   params.append(filters["category"])
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY i.reported_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_issue(issue_id):
    conn = get_conn()
    row = conn.execute("""
        SELECT i.*, u.name AS citizen_name, w.name AS worker_name,
               wu.dept AS worker_dept
        FROM issues i
        LEFT JOIN users u  ON i.citizen_id = u.id
        LEFT JOIN users w  ON i.worker_id  = w.id
        LEFT JOIN users wu ON i.worker_id  = wu.id
        WHERE i.id = ?
    """, (issue_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def assign_worker(issue_id, worker_id, worker_name, dept):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    conn.execute("""
        UPDATE issues SET worker_id=?, status='assigned', assigned_at=?
        WHERE id=?
    """, (worker_id, now, issue_id))
    conn.execute(
        "INSERT INTO timeline (issue_id, text, color, created_at) VALUES (?,?,?,?)",
        (issue_id, f"Assigned to {worker_name} ({dept} dept.)", "#a855f7", now)
    )
    conn.commit()
    conn.close()


def resolve_issue(issue_id, worker_name, after_image_bytes):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    conn.execute("""
        UPDATE issues SET status='resolved', resolved_at=?, after_image=?
        WHERE id=?
    """, (now, after_image_bytes, issue_id))
    conn.execute(
        "INSERT INTO timeline (issue_id, text, color, created_at) VALUES (?,?,?,?)",
        (issue_id, f"Work completed — after photo uploaded by {worker_name}", "#22c55e", now)
    )
    conn.commit()
    conn.close()


def get_timeline(issue_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM timeline WHERE issue_id=? ORDER BY created_at ASC",
        (issue_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_workers():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM users WHERE role='worker'").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats(filters=None):
    issues = get_issues(filters)
    return {
        "total":    len(issues),
        "pending":  sum(1 for i in issues if i["status"] == "pending"),
        "assigned": sum(1 for i in issues if i["status"] == "assigned"),
        "resolved": sum(1 for i in issues if i["status"] == "resolved"),
    }
