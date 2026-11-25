"""Run from the project root:  python -m unittest tests.test_database -v"""

import os
import shutil
import tempfile
import unittest

import database
from database import DatabaseError


class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Each test uses a brand-new temporary database file.
        self.folder = tempfile.mkdtemp()
        database.DB_PATH = os.path.join(self.folder, "test.db")
        database.init_db()

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    # ---------- subjects ----------
    def test_add_and_get_subject(self):
        sid = database.add_subject("Data Structures", "CSE201", "Trees, graphs")
        subject = database.get_subject(sid)
        self.assertEqual(subject["subject_name"], "Data Structures")
        self.assertEqual(subject["course_code"], "CSE201")
        self.assertEqual(len(database.get_all_subjects()), 1)

    def test_duplicate_subject_name_rejected(self):
        database.add_subject("Operating Systems")
        with self.assertRaises(DatabaseError):
            database.add_subject("operating systems")  # different case

    def test_duplicate_course_code_rejected(self):
        database.add_subject("DBMS", "CSE301")
        with self.assertRaises(DatabaseError):
            database.add_subject("Networks", "cse301")

    def test_empty_course_code_allowed_many_times(self):
        database.add_subject("Subject A")
        database.add_subject("Subject B")
        self.assertEqual(len(database.get_all_subjects()), 2)

    def test_empty_subject_name_rejected(self):
        with self.assertRaises(DatabaseError):
            database.add_subject("   ")

    def test_update_subject(self):
        sid = database.add_subject("Old Name")
        database.update_subject(sid, "New Name", "X1", "desc")
        self.assertEqual(database.get_subject(sid)["subject_name"], "New Name")

    def test_update_missing_subject(self):
        with self.assertRaises(DatabaseError):
            database.update_subject(999, "Nope")

    def test_search_subjects(self):
        database.add_subject("Computer Networks", "CSE401")
        database.add_subject("Software Engineering", "CSE305")
        self.assertEqual(len(database.search_subjects("network")), 1)
        self.assertEqual(len(database.search_subjects("CSE3")), 1)
        self.assertEqual(database.search_subjects("zzz"), [])

    def test_delete_subject_cascades(self):
        sid = database.add_subject("DSA")
        tid = database.add_topic(sid, "Arrays", 30, "High", "2026-12-01")
        database.add_session(tid, 30)
        database.delete_subject(sid)
        self.assertEqual(database.get_topics(), [])
        self.assertEqual(database.get_sessions(), [])

    # ---------- topics ----------
    def test_add_and_get_topic(self):
        sid = database.add_subject("DSA")
        tid = database.add_topic(sid, "Arrays", "45", "High", "2026-12-01")
        topic = database.get_topic(tid)
        self.assertEqual(topic["estimated_duration"], 45)
        self.assertEqual(topic["status"], "Pending")
        self.assertEqual(topic["subject_name"], "DSA")

    def test_topic_needs_existing_subject(self):
        with self.assertRaises(DatabaseError):
            database.add_topic(999, "Ghost", 30, "Low")

    def test_topic_validation(self):
        sid = database.add_subject("DSA")
        with self.assertRaises(DatabaseError):
            database.add_topic(sid, "A", 0, "High")
        with self.assertRaises(DatabaseError):
            database.add_topic(sid, "A", -5, "High")
        with self.assertRaises(DatabaseError):
            database.add_topic(sid, "A", "abc", "High")
        with self.assertRaises(DatabaseError):
            database.add_topic(sid, "A", 30, "Urgent")
        with self.assertRaises(DatabaseError):
            database.add_topic(sid, "A", 30, "High", "31-12-2026")
        with self.assertRaises(DatabaseError):
            database.add_topic(sid, "A", 30, "High", "2026-02-30")
        self.assertEqual(database.get_topics(), [])

    def test_duplicate_topic_in_same_subject(self):
        sid = database.add_subject("DSA")
        database.add_topic(sid, "Arrays", 30, "High")
        with self.assertRaises(DatabaseError):
            database.add_topic(sid, "arrays", 20, "Low")
        other = database.add_subject("DBMS")
        database.add_topic(other, "Arrays", 20, "Low")  # allowed: other subject

    def test_update_and_status(self):
        sid = database.add_subject("DSA")
        tid = database.add_topic(sid, "Arrays", 30, "High")
        database.update_topic(tid, sid, "Arrays & Strings", 60, "Medium", "2026-12-10")
        topic = database.get_topic(tid)
        self.assertEqual(topic["topic_name"], "Arrays & Strings")
        self.assertEqual(topic["estimated_duration"], 60)
        database.set_topic_status(tid, "Completed")
        self.assertEqual(database.get_topic(tid)["status"], "Completed")
        database.set_topic_status(tid, "Pending")
        self.assertEqual(database.get_topic(tid)["status"], "Pending")
        with self.assertRaises(DatabaseError):
            database.set_topic_status(tid, "Done")

    def test_filters(self):
        s1 = database.add_subject("DSA")
        s2 = database.add_subject("DBMS")
        t1 = database.add_topic(s1, "Arrays", 30, "High")
        database.add_topic(s1, "Trees", 40, "Low")
        database.add_topic(s2, "SQL", 50, "High")
        database.set_topic_status(t1, "Completed")
        self.assertEqual(len(database.get_topics(subject_id=s1)), 2)
        self.assertEqual(len(database.get_topics(priority="High")), 2)
        self.assertEqual(len(database.get_topics(status="Completed")), 1)
        self.assertEqual(len(database.get_pending_topics()), 2)
        self.assertEqual(len(database.get_topics(keyword="sql")), 1)
        self.assertEqual(len(database.get_topics(keyword="DBMS")), 1)

    def test_delete_topic(self):
        sid = database.add_subject("DSA")
        tid = database.add_topic(sid, "Arrays", 30, "High")
        database.delete_topic(tid)
        self.assertIsNone(database.get_topic(tid))
        with self.assertRaises(DatabaseError):
            database.delete_topic(tid)

    # ---------- persistence ----------
    def test_data_persists_after_reconnect(self):
        sid = database.add_subject("DSA")
        database.add_topic(sid, "Arrays", 30, "High")
        # Every call opens a NEW connection, so reading again proves the data
        # was saved to the file. init_db() again must not erase anything.
        database.init_db()
        self.assertEqual(len(database.get_all_subjects()), 1)
        self.assertEqual(len(database.get_topics()), 1)

    # ---------- sessions ----------
    def test_sessions(self):
        sid = database.add_subject("DSA")
        tid = database.add_topic(sid, "Arrays", 30, "High")
        s1 = database.add_session(tid, 30, "2026-12-01", "09:00", "09:30")
        database.add_session(tid, 20)  # no date/time is allowed
        self.assertEqual(len(database.get_sessions()), 2)
        self.assertEqual(len(database.get_sessions(session_date="2026-12-01")), 1)
        database.set_session_status(s1, "Completed")
        self.assertEqual(len(database.get_sessions(status="Completed")), 1)
        database.clear_pending_sessions()
        self.assertEqual(len(database.get_sessions()), 1)
        with self.assertRaises(DatabaseError):
            database.add_session(tid, 30, "2026-12-01", "9am", "")
        with self.assertRaises(DatabaseError):
            database.add_session(999, 30)  # topic does not exist


if __name__ == "__main__":
    unittest.main()