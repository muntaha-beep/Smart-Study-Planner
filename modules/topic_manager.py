"""
topic_manager.py - business logic for study topics (Phase 4).

The GUI talks to this class. It checks the input, calls database.py to store
or read topics, and uses our own sorting algorithms to order the topic lists.
Every problem is reported by raising DatabaseError with a friendly message.
"""

from datetime import date, datetime

import database
from database import DatabaseError
from algorithms.merge_sort import merge_sort_topics
from algorithms.insertion_sort import insertion_sort_topics
from algorithms.quick_sort import quick_sort_topics
from algorithms.heap_sort import heap_sort_topics

MAX_NAME_LENGTH = 100
MAX_DURATION = 1440  # minutes (24 hours) for one topic

# Names the GUI can show in a "sort with" drop-down.
SORT_ALGORITHMS = {
    "Merge Sort": merge_sort_topics,
    "Insertion Sort": insertion_sort_topics,
    "Quick Sort": quick_sort_topics,
    "Heap Sort": heap_sort_topics,
}

# What the GUI can show in a "sort by" drop-down -> the criterion text.
SORT_CRITERIA = {
    "Deadline": "deadline",
    "Priority": "priority",
    "Duration": "duration",
    "Name": "name",
}


class TopicManager:
    """Add, view, edit, search, filter, sort, complete and delete topics."""

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _validate(self, subject_id, name, duration, priority, deadline):
        """Check and clean all topic fields. Returns the cleaned values."""
        if database.get_subject(subject_id) is None:
            raise DatabaseError("Please choose an existing subject.")

        name = (name or "").strip()
        if name == "":
            raise DatabaseError("Topic name is required.")
        if len(name) > MAX_NAME_LENGTH:
            raise DatabaseError("Topic name must be at most "
                                + str(MAX_NAME_LENGTH) + " characters.")

        minutes = database.validate_duration(duration)
        if minutes > MAX_DURATION:
            raise DatabaseError("Duration cannot be more than "
                                + str(MAX_DURATION) + " minutes.")

        priority = (priority or "").strip().capitalize()  # "high" -> "High"
        if priority not in database.PRIORITIES:
            raise DatabaseError("Priority must be High, Medium or Low.")

        deadline = database.validate_date(deadline)  # None if empty
        return name, minutes, priority, deadline

    # ------------------------------------------------------------------
    # Add / edit / delete
    # ------------------------------------------------------------------
    def add_topic(self, subject_id, name, duration, priority, deadline=""):
        """Add a topic and return its new topic_id."""
        name, minutes, priority, deadline = self._validate(
            subject_id, name, duration, priority, deadline)
        return database.add_topic(subject_id, name, minutes, priority, deadline or "")

    def update_topic(self, topic_id, subject_id, name, duration, priority, deadline=""):
        """Change a topic's details (its completion status is not changed)."""
        self.get_topic(topic_id)  # clear error if it does not exist
        name, minutes, priority, deadline = self._validate(
            subject_id, name, duration, priority, deadline)
        database.update_topic(topic_id, subject_id, name, minutes, priority, deadline or "")

    def delete_topic(self, topic_id):
        database.delete_topic(topic_id)

    def get_topic(self, topic_id):
        """Return one topic (with its subject_name) or raise DatabaseError."""
        topic = database.get_topic(topic_id)
        if topic is None:
            raise DatabaseError("Topic not found.")
        return topic

    # ------------------------------------------------------------------
    # Completion status
    # ------------------------------------------------------------------
    def mark_completed(self, topic_id):
        database.set_topic_status(topic_id, "Completed")

    def mark_pending(self, topic_id):
        database.set_topic_status(topic_id, "Pending")

    def toggle_status(self, topic_id):
        """Switch Pending <-> Completed. Returns the new status."""
        topic = self.get_topic(topic_id)
        new_status = "Pending" if topic["status"] == "Completed" else "Completed"
        database.set_topic_status(topic_id, new_status)
        return new_status

    # ------------------------------------------------------------------
    # Listing: filter, search and sort
    # ------------------------------------------------------------------
    def list_topics(self, subject_id=None, priority=None, status=None,
                    keyword="", sort_by=None, algorithm="Merge Sort"):
        """
        Get topics. Every argument is optional.

        subject_id : only topics of this subject
        priority   : "High", "Medium" or "Low"
        status     : "Pending" or "Completed"
        keyword    : text to look for in the topic or subject name
        sort_by    : "Deadline", "Priority", "Duration" or "Name" (or None)
        algorithm  : which of OUR sorting algorithms to use (see SORT_ALGORITHMS)
        """
        topics = database.get_topics(subject_id=subject_id, priority=priority,
                                     status=status, keyword=keyword)
        if sort_by is None:
            return topics

        if sort_by not in SORT_CRITERIA:
            raise DatabaseError("Cannot sort by: " + str(sort_by))
        if algorithm not in SORT_ALGORITHMS:
            raise DatabaseError("Unknown sorting algorithm: " + str(algorithm))
        return SORT_ALGORITHMS[algorithm](topics, SORT_CRITERIA[sort_by])

    # ------------------------------------------------------------------
    # Deadline helpers
    # ------------------------------------------------------------------
    def days_until_deadline(self, topic, today=None):
        """Days from today to the deadline (negative = late). None if no deadline."""
        if not topic["deadline"]:
            return None
        today = today or date.today()
        deadline = datetime.strptime(topic["deadline"], "%Y-%m-%d").date()
        return (deadline - today).days

    def is_overdue(self, topic, today=None):
        """True for a pending topic whose deadline has already passed."""
        days = self.days_until_deadline(topic, today)
        return topic["status"] == "Pending" and days is not None and days < 0


# ----------------------------------------------------------------------
# Demo: run with   python -m modules.topic_manager
# (uses a temporary database, so your real data is not touched)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import shutil
    import tempfile

    folder = tempfile.mkdtemp()
    database.DB_PATH = os.path.join(folder, "demo.db")
    database.init_db()

    dsa = database.add_subject("Data Structures", "CSE201")
    dbms = database.add_subject("DBMS", "CSE301")
    manager = TopicManager()

    def show(topics):
        for t in topics:
            print("  ", t["topic_name"].ljust(8), t["subject_name"].ljust(16),
                  str(t["estimated_duration"]).rjust(3), "min ", t["priority"].ljust(6),
                  str(t["deadline"]).ljust(10), t["status"])

    print("--- Add topics (priority typed in lowercase is fixed automatically) ---")
    manager.add_topic(dsa, "Trees", "60", "high", "2026-12-05")
    arrays = manager.add_topic(dsa, "Arrays", 30, "Low")
    manager.add_topic(dbms, "SQL", 45, "Medium", "2026-12-01")
    manager.add_topic(dbms, "Joins", 50, "High", "2026-12-03")
    show(manager.list_topics())

    print("\n--- Invalid input ---")
    bad_inputs = [
        (dsa, "", 30, "High", ""),
        (dsa, "X", 0, "High", ""),
        (dsa, "X", "abc", "High", ""),
        (dsa, "X", 2000, "High", ""),
        (dsa, "X", 30, "Urgent", ""),
        (dsa, "X", 30, "High", "05-12-2026"),
        (999, "X", 30, "High", ""),
        (dsa, "trees", 20, "Low", ""),
    ]
    for args in bad_inputs:
        try:
            manager.add_topic(*args)
        except DatabaseError as error:
            print("Rejected:", error)

    print("\n--- Sort by Deadline (Heap Sort), then Duration (Quick Sort) ---")
    show(manager.list_topics(sort_by="Deadline", algorithm="Heap Sort"))
    print()
    show(manager.list_topics(sort_by="Duration", algorithm="Quick Sort"))

    print("\n--- Filters and search ---")
    print("High priority :", [t["topic_name"] for t in manager.list_topics(priority="High")])
    print("Subject DBMS  :", [t["topic_name"] for t in manager.list_topics(subject_id=dbms)])
    print("Search 'sql'  :", [t["topic_name"] for t in manager.list_topics(keyword="sql")])

    print("\n--- Complete / pending ---")
    print("Toggle Arrays ->", manager.toggle_status(arrays))
    print("Completed     :", [t["topic_name"] for t in manager.list_topics(status="Completed")])
    print("Toggle again  ->", manager.toggle_status(arrays))

    print("\n--- Edit ---")
    manager.update_topic(arrays, dsa, "Arrays & Strings", 40, "Medium", "2026-11-30")
    print(manager.get_topic(arrays)["topic_name"], manager.get_topic(arrays)["estimated_duration"])

    print("\n--- Deadlines (pretend today is 2026-12-01) ---")
    today = date(2026, 12, 1)
    for t in manager.list_topics(sort_by="Deadline"):
        print("  ", t["topic_name"].ljust(16), "days left:", manager.days_until_deadline(t, today),
              "| overdue:", manager.is_overdue(t, today))

    print("\n--- Delete ---")
    manager.delete_topic(arrays)
    print("Topics left:", len(manager.list_topics()))
    try:
        manager.delete_topic(arrays)
    except DatabaseError as error:
        print("Delete again:", error)

    shutil.rmtree(folder, ignore_errors=True)