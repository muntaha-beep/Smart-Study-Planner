"""
database.py - all SQLite code lives here (Phase 2).

Other files never write SQL. They call the functions in this file.
Every query is parameterized (uses ?) to stay safe from SQL injection.
"""

import os
import sqlite3
from datetime import datetime

# The database file is stored next to this file.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "study_planner.db")

PRIORITIES = ("High", "Medium", "Low")
TOPIC_STATUSES = ("Pending", "Completed")
SESSION_STATUSES = ("Pending", "Completed")


class DatabaseError(Exception):
    """Raised with a friendly message when something goes wrong."""


# ----------------------------------------------------------------------
# Connection helpers
# ----------------------------------------------------------------------
def get_connection():
    """Open a connection and turn ON foreign key checking."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # lets us read columns by name
    return conn


def _execute(query, params=()):
    """Run INSERT / UPDATE / DELETE. Returns (last_row_id, rows_changed)."""
    conn = get_connection()
    try:
        cur = conn.execute(query, params)
        conn.commit()
        return cur.lastrowid, cur.rowcount
    except sqlite3.IntegrityError as error:
        conn.rollback()
        message = str(error)
        if "UNIQUE" in message:
            raise DatabaseError("This record already exists (duplicate value).")
        if "FOREIGN KEY" in message:
            raise DatabaseError("Related record not found (invalid subject/topic).")
        raise DatabaseError("Invalid data: " + message)
    except sqlite3.Error as error:
        conn.rollback()
        raise DatabaseError("Database error: " + str(error))
    finally:
        conn.close()


def _fetch_all(query, params=()):
    """Run SELECT. Returns a list of dictionaries."""
    conn = get_connection()
    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as error:
        raise DatabaseError("Database error: " + str(error))
    finally:
        conn.close()


def _fetch_one(query, params=()):
    """Run SELECT. Returns one dictionary or None."""
    rows = _fetch_all(query, params)
    return rows[0] if rows else None


# ----------------------------------------------------------------------
# Validation helpers
# ----------------------------------------------------------------------
def validate_date(text):
    """Return the date as 'YYYY-MM-DD' or raise DatabaseError. Empty -> None."""
    text = (text or "").strip()
    if text == "":
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise DatabaseError("Date must be a real date in YYYY-MM-DD format.")


def validate_time(text):
    """Return the time as 'HH:MM' or raise DatabaseError. Empty -> None."""
    text = (text or "").strip()
    if text == "":
        return None
    try:
        return datetime.strptime(text, "%H:%M").strftime("%H:%M")
    except ValueError:
        raise DatabaseError("Time must be in HH:MM (24-hour) format.")


def validate_duration(value):
    """Duration must be a positive whole number of minutes."""
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        raise DatabaseError("Duration must be a whole number of minutes.")
    if minutes <= 0:
        raise DatabaseError("Duration must be greater than zero.")
    return minutes


def _clean_text(value):
    return (value or "").strip()


# ----------------------------------------------------------------------
# Create tables
# ----------------------------------------------------------------------
def init_db():
    """Create the database file and all tables (safe to call every time)."""
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                course_code  TEXT COLLATE NOCASE UNIQUE,
                description  TEXT
            );

            CREATE TABLE IF NOT EXISTS topics (
                topic_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id         INTEGER NOT NULL,
                topic_name         TEXT NOT NULL COLLATE NOCASE,
                estimated_duration INTEGER NOT NULL CHECK (estimated_duration > 0),
                priority           TEXT NOT NULL
                                   CHECK (priority IN ('High', 'Medium', 'Low')),
                deadline           TEXT,
                status             TEXT NOT NULL DEFAULT 'Pending'
                                   CHECK (status IN ('Pending', 'Completed')),
                created_at         TEXT NOT NULL,
                FOREIGN KEY (subject_id) REFERENCES subjects (subject_id)
                    ON DELETE CASCADE,
                UNIQUE (subject_id, topic_name)
            );

            CREATE TABLE IF NOT EXISTS study_sessions (
                session_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id           INTEGER NOT NULL,
                session_date       TEXT,
                start_time         TEXT,
                end_time           TEXT,
                allocated_duration INTEGER NOT NULL CHECK (allocated_duration > 0),
                status             TEXT NOT NULL DEFAULT 'Pending'
                                   CHECK (status IN ('Pending', 'Completed')),
                FOREIGN KEY (topic_id) REFERENCES topics (topic_id)
                    ON DELETE CASCADE
            );
            """
        )
        conn.commit()
    except sqlite3.Error as error:
        raise DatabaseError("Could not create tables: " + str(error))
    finally:
        conn.close()


# ----------------------------------------------------------------------
# SUBJECTS
# ----------------------------------------------------------------------
def add_subject(name, course_code="", description=""):
    """Add a subject. Returns the new subject_id."""
    name = _clean_text(name)
    if name == "":
        raise DatabaseError("Subject name is required.")
    code = _clean_text(course_code) or None  # empty code is stored as NULL
    new_id, _ = _execute(
        "INSERT INTO subjects (subject_name, course_code, description) VALUES (?, ?, ?)",
        (name, code, _clean_text(description)),
    )
    return new_id


def get_subject(subject_id):
    return _fetch_one("SELECT * FROM subjects WHERE subject_id = ?", (subject_id,))


def get_all_subjects():
    return _fetch_all("SELECT * FROM subjects ORDER BY subject_name")


def search_subjects(keyword):
    like = "%" + _clean_text(keyword) + "%"
    return _fetch_all(
        """SELECT * FROM subjects
           WHERE subject_name LIKE ? OR IFNULL(course_code, '') LIKE ?
           ORDER BY subject_name""",
        (like, like),
    )


def update_subject(subject_id, name, course_code="", description=""):
    name = _clean_text(name)
    if name == "":
        raise DatabaseError("Subject name is required.")
    code = _clean_text(course_code) or None
    _, changed = _execute(
        """UPDATE subjects SET subject_name = ?, course_code = ?, description = ?
           WHERE subject_id = ?""",
        (name, code, _clean_text(description), subject_id),
    )
    if changed == 0:
        raise DatabaseError("Subject not found.")


def delete_subject(subject_id):
    """Deletes the subject AND all its topics and sessions (CASCADE)."""
    _, changed = _execute("DELETE FROM subjects WHERE subject_id = ?", (subject_id,))
    if changed == 0:
        raise DatabaseError("Subject not found.")


# ----------------------------------------------------------------------
# TOPICS
# ----------------------------------------------------------------------
def _check_priority(priority):
    if priority not in PRIORITIES:
        raise DatabaseError("Priority must be High, Medium or Low.")


def add_topic(subject_id, name, duration, priority, deadline=""):
    """Add a topic. Returns the new topic_id."""
    name = _clean_text(name)
    if name == "":
        raise DatabaseError("Topic name is required.")
    minutes = validate_duration(duration)
    _check_priority(priority)
    deadline = validate_date(deadline)
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_id, _ = _execute(
        """INSERT INTO topics
           (subject_id, topic_name, estimated_duration, priority, deadline, status, created_at)
           VALUES (?, ?, ?, ?, ?, 'Pending', ?)""",
        (subject_id, name, minutes, priority, deadline, created),
    )
    return new_id


_TOPIC_SELECT = """
    SELECT t.*, s.subject_name
    FROM topics t JOIN subjects s ON t.subject_id = s.subject_id
"""


def get_topic(topic_id):
    return _fetch_one(_TOPIC_SELECT + " WHERE t.topic_id = ?", (topic_id,))


def get_topics(subject_id=None, priority=None, status=None, keyword=None):
    """Get topics. Every argument is an optional filter."""
    query = _TOPIC_SELECT + " WHERE 1 = 1"
    params = []
    if subject_id is not None:
        query += " AND t.subject_id = ?"
        params.append(subject_id)
    if priority:
        query += " AND t.priority = ?"
        params.append(priority)
    if status:
        query += " AND t.status = ?"
        params.append(status)
    if keyword and keyword.strip():
        query += " AND (t.topic_name LIKE ? OR s.subject_name LIKE ?)"
        like = "%" + keyword.strip() + "%"
        params.extend([like, like])
    query += " ORDER BY t.topic_id"
    return _fetch_all(query, tuple(params))


def get_pending_topics():
    """Used by the study plan generator (Phase 4)."""
    return get_topics(status="Pending")


def update_topic(topic_id, subject_id, name, duration, priority, deadline=""):
    name = _clean_text(name)
    if name == "":
        raise DatabaseError("Topic name is required.")
    minutes = validate_duration(duration)
    _check_priority(priority)
    deadline = validate_date(deadline)
    _, changed = _execute(
        """UPDATE topics SET subject_id = ?, topic_name = ?, estimated_duration = ?,
           priority = ?, deadline = ? WHERE topic_id = ?""",
        (subject_id, name, minutes, priority, deadline, topic_id),
    )
    if changed == 0:
        raise DatabaseError("Topic not found.")


def set_topic_status(topic_id, status):
    if status not in TOPIC_STATUSES:
        raise DatabaseError("Status must be Pending or Completed.")
    _, changed = _execute(
        "UPDATE topics SET status = ? WHERE topic_id = ?", (status, topic_id)
    )
    if changed == 0:
        raise DatabaseError("Topic not found.")


def delete_topic(topic_id):
    _, changed = _execute("DELETE FROM topics WHERE topic_id = ?", (topic_id,))
    if changed == 0:
        raise DatabaseError("Topic not found.")


# ----------------------------------------------------------------------
# STUDY SESSIONS
# ----------------------------------------------------------------------
def add_session(topic_id, allocated_duration, session_date="", start_time="", end_time=""):
    """Add a study session. Date/time are optional. Returns the new session_id."""
    minutes = validate_duration(allocated_duration)
    new_id, _ = _execute(
        """INSERT INTO study_sessions
           (topic_id, session_date, start_time, end_time, allocated_duration, status)
           VALUES (?, ?, ?, ?, ?, 'Pending')""",
        (
            topic_id,
            validate_date(session_date),
            validate_time(start_time),
            validate_time(end_time),
            minutes,
        ),
    )
    return new_id


_SESSION_SELECT = """
    SELECT ss.*, t.topic_name, t.priority, s.subject_name
    FROM study_sessions ss
    JOIN topics t ON ss.topic_id = t.topic_id
    JOIN subjects s ON t.subject_id = s.subject_id
"""


def get_sessions(session_date=None, status=None):
    query = _SESSION_SELECT + " WHERE 1 = 1"
    params = []
    if session_date:
        query += " AND ss.session_date = ?"
        params.append(session_date)
    if status:
        query += " AND ss.status = ?"
        params.append(status)
    query += " ORDER BY ss.session_date, ss.start_time, ss.session_id"
    return _fetch_all(query, tuple(params))


def set_session_status(session_id, status):
    if status not in SESSION_STATUSES:
        raise DatabaseError("Status must be Pending or Completed.")
    _, changed = _execute(
        "UPDATE study_sessions SET status = ? WHERE session_id = ?", (status, session_id)
    )
    if changed == 0:
        raise DatabaseError("Session not found.")


def delete_session(session_id):
    _, changed = _execute("DELETE FROM study_sessions WHERE session_id = ?", (session_id,))
    if changed == 0:
        raise DatabaseError("Session not found.")


def clear_pending_sessions():
    """Remove old pending sessions before saving a regenerated plan."""
    _execute("DELETE FROM study_sessions WHERE status = 'Pending'")