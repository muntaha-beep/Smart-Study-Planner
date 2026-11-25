"""
subject_manager.py - business logic for subjects (Phase 4).

The GUI talks to this class. This class checks the input, then calls
database.py to read or write the data.
Every problem is reported by raising DatabaseError with a friendly message,
so the GUI only needs to catch ONE kind of error.
"""

import database
from database import DatabaseError

MAX_NAME_LENGTH = 100
MAX_CODE_LENGTH = 20
MAX_DESCRIPTION_LENGTH = 300


class SubjectManager:
    """Add, view, edit, search and delete subjects."""

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _validate(self, name, course_code, description):
        """Clean the text and check the length limits. Returns cleaned values."""
        name = (name or "").strip()
        course_code = (course_code or "").strip()
        description = (description or "").strip()

        if name == "":
            raise DatabaseError("Subject name is required.")
        if len(name) > MAX_NAME_LENGTH:
            raise DatabaseError("Subject name must be at most "
                                + str(MAX_NAME_LENGTH) + " characters.")
        if len(course_code) > MAX_CODE_LENGTH:
            raise DatabaseError("Course code must be at most "
                                + str(MAX_CODE_LENGTH) + " characters.")
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise DatabaseError("Description must be at most "
                                + str(MAX_DESCRIPTION_LENGTH) + " characters.")
        return name, course_code, description

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------
    def add_subject(self, name, course_code="", description=""):
        """Add a subject and return its new subject_id."""
        name, course_code, description = self._validate(name, course_code, description)
        return database.add_subject(name, course_code, description)

    def get_subject(self, subject_id):
        """Return one subject, or raise DatabaseError if it does not exist."""
        subject = database.get_subject(subject_id)
        if subject is None:
            raise DatabaseError("Subject not found.")
        return subject

    def list_subjects(self, keyword=""):
        """All subjects (A-Z), or only those matching the search keyword."""
        if keyword and keyword.strip():
            return database.search_subjects(keyword)
        return database.get_all_subjects()

    def list_subjects_with_counts(self, keyword=""):
        """
        Like list_subjects, but every subject also gets:
          "topic_count"     : how many topics it has
          "completed_count" : how many of them are completed
        """
        result = []
        for subject in self.list_subjects(keyword):
            topics = database.get_topics(subject_id=subject["subject_id"])
            completed = 0
            for topic in topics:
                if topic["status"] == "Completed":
                    completed += 1
            row = dict(subject)
            row["topic_count"] = len(topics)
            row["completed_count"] = completed
            result.append(row)
        return result

    def update_subject(self, subject_id, name, course_code="", description=""):
        """Change a subject's details."""
        name, course_code, description = self._validate(name, course_code, description)
        database.update_subject(subject_id, name, course_code, description)

    def count_topics(self, subject_id):
        """How many topics belong to this subject (for the delete warning)."""
        return len(database.get_topics(subject_id=subject_id))

    def delete_subject(self, subject_id):
        """
        Delete a subject together with all its topics and sessions.
        Returns the number of topics that were deleted with it.
        """
        self.get_subject(subject_id)  # raises a clear error if it does not exist
        deleted_topics = self.count_topics(subject_id)
        database.delete_subject(subject_id)
        return deleted_topics


# ----------------------------------------------------------------------
# Demo: run with   python -m modules.subject_manager
# (uses a temporary database, so your real data is not touched)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import shutil
    import tempfile

    folder = tempfile.mkdtemp()
    database.DB_PATH = os.path.join(folder, "demo.db")
    database.init_db()

    manager = SubjectManager()

    print("--- Add subjects ---")
    dsa = manager.add_subject("Data Structures and Algorithms", "CSE201", "Trees, graphs")
    dbms = manager.add_subject("Database Management Systems", "CSE301")
    manager.add_subject("Operating Systems")
    print("Subjects:", [s["subject_name"] for s in manager.list_subjects()])

    print("\n--- Duplicate and invalid input ---")
    for args in [("data structures and algorithms",), ("New", "cse201"), ("   ",),
                 ("A" * 101,), ("Valid name", "X" * 21)]:
        try:
            manager.add_subject(*args)
        except DatabaseError as error:
            print("Rejected:", error)

    print("\n--- Search ---")
    print("'data'   ->", [s["subject_name"] for s in manager.list_subjects("data")])
    print("'cse3'   ->", [s["subject_name"] for s in manager.list_subjects("cse3")])
    print("'nothing'->", manager.list_subjects("nothing"))

    print("\n--- Edit ---")
    manager.update_subject(dbms, "DBMS", "CSE301", "SQL and normalization")
    print(manager.get_subject(dbms))

    print("\n--- Topic counts and delete ---")
    t1 = database.add_topic(dsa, "Arrays", 30, "High")
    database.add_topic(dsa, "Trees", 45, "Medium")
    database.set_topic_status(t1, "Completed")
    for row in manager.list_subjects_with_counts():
        print(row["subject_name"], "| topics:", row["topic_count"],
              "| completed:", row["completed_count"])
    print("Deleted topics with subject:", manager.delete_subject(dsa))
    print("Subjects left:", [s["subject_name"] for s in manager.list_subjects()])
    try:
        manager.delete_subject(dsa)
    except DatabaseError as error:
        print("Delete again:", error)

    shutil.rmtree(folder, ignore_errors=True)