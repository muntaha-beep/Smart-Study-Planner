"""
schedule_manager.py - business logic for the study schedule (Phase 4).

A "session" is one planned study period for one topic on one date. Sessions
are stored in the study_sessions table.

What this class does:
  * saves a generated plan as sessions for a chosen date
  * refuses to save timed sessions that would OVERLAP other sessions that day
  * lists sessions (all, one day, or pending only)
  * marks sessions completed or pending again
If a session has no clock time, none is invented: it is shown in order with
its allocated duration only.
"""

from datetime import date

import database
from database import DatabaseError
from algorithms.merge_sort import merge_sort
from algorithms.activity_selection import time_to_minutes


class ScheduleManager:
    """Save, view and update study sessions."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _check_date(self, session_date):
        """Return a valid 'YYYY-MM-DD' date text; a date is required."""
        if isinstance(session_date, date):
            session_date = session_date.strftime("%Y-%m-%d")
        checked = database.validate_date(session_date)
        if checked is None:
            raise DatabaseError("Please enter a session date (YYYY-MM-DD).")
        return checked

    def _decorate(self, session):
        """Copy a session and add display fields."""
        row = dict(session)
        if row["start_time"] and row["end_time"]:
            row["time_label"] = row["start_time"] + "-" + row["end_time"]
        else:
            row["time_label"] = "No clock time"
        row["is_completed"] = row["status"] == "Completed"
        return row

    def find_overlaps(self, sessions):
        """
        Find sessions whose clock times overlap.
        sessions: dicts with "start_time" and "end_time" ('HH:MM' or None).
        Returns a list of (first_session, second_session) pairs.
        Sessions without clock times cannot overlap and are ignored.
        Sessions that only touch (one ends 10:00, next starts 10:00) are fine.
        """
        timed = []
        for session in sessions:
            if session.get("start_time") and session.get("end_time"):
                item = dict(session)
                item["_start"] = time_to_minutes(session["start_time"])
                item["_finish"] = time_to_minutes(session["end_time"])
                timed.append(item)

        timed = merge_sort(timed, key=lambda s: s["_start"])  # our own sort

        overlaps = []
        last = None  # the session seen so far that ends latest
        for current in timed:
            if last is not None and current["_start"] < last["_finish"]:
                overlaps.append((last, current))
            if last is None or current["_finish"] > last["_finish"]:
                last = current
        return overlaps

    def _name_with_time(self, session):
        return "'" + session["topic_name"] + "' (" + session["start_time"] + "-" + session["end_time"] + ")"

    # ------------------------------------------------------------------
    # Saving a plan
    # ------------------------------------------------------------------
    def busy_slots_for_date(self, session_date):
        """
        Clock times already used on a date by COMPLETED sessions.
        Pass this to StudyPlanner.generate_plan(busy_slots=...) so a new plan
        does not collide with them. (Pending sessions are not included because
        saving a new plan replaces them.)
        """
        session_date = self._check_date(session_date)
        return [s for s in database.get_sessions(session_date=session_date, status="Completed")
                if s["start_time"] and s["end_time"]]

    def save_plan(self, plan, session_date):
        """
        Save the selected topics of a plan as sessions on session_date.

        Pending sessions already saved for that date are replaced (so
        regenerating a plan never creates duplicates). Completed sessions are kept.
        Raises DatabaseError, and saves nothing, if the new timed sessions would
        overlap a kept session. Returns the number of sessions saved.
        """
        session_date = self._check_date(session_date)
        if not plan or not plan.get("selected"):
            raise DatabaseError("The plan has no sessions to save.")

        # Check for overlaps BEFORE changing anything.
        kept = database.get_sessions(session_date=session_date, status="Completed")
        new_sessions = []
        for topic in plan["selected"]:
            new_sessions.append({"topic_name": topic["topic_name"],
                                 "start_time": topic.get("start_time"),
                                 "end_time": topic.get("end_time")})
        overlaps = self.find_overlaps(kept + new_sessions)
        if overlaps:
            first, second = overlaps[0]
            raise DatabaseError("Cannot save: " + self._name_with_time(first) + " overlaps "
                                + self._name_with_time(second) + ". "
                                "Generate the plan again with a different start time.")

        # Replace this date's pending sessions, then save the new ones.
        for old in database.get_sessions(session_date=session_date, status="Pending"):
            database.delete_session(old["session_id"])
        for topic in plan["selected"]:
            database.add_session(topic["topic_id"], topic["allocated_duration"], session_date,
                                 topic.get("start_time") or "", topic.get("end_time") or "")
        return len(plan["selected"])

    # ------------------------------------------------------------------
    # Viewing
    # ------------------------------------------------------------------
    def get_schedule(self, session_date=None, status=None):
        """
        Sessions with topic and subject names, oldest date first.
        session_date : only this date (YYYY-MM-DD), or None for all dates
        status       : "Pending", "Completed" or None
        """
        if session_date is not None and session_date != "":
            session_date = self._check_date(session_date)
        else:
            session_date = None
        sessions = database.get_sessions(session_date=session_date, status=status)
        return [self._decorate(s) for s in sessions]

    def get_daily_sessions(self, session_date):
        """All sessions of one date."""
        return self.get_schedule(session_date=session_date)

    def get_pending_sessions(self):
        """Every session that is not completed yet, on any date."""
        return self.get_schedule(status="Pending")

    def list_session_dates(self):
        """The dates that have sessions, in order (for a date drop-down)."""
        dates = []
        for session in database.get_sessions():
            if session["session_date"] and session["session_date"] not in dates:
                dates.append(session["session_date"])
        return dates

    def day_summary(self, session_date):
        """Counts and minutes for one day."""
        sessions = self.get_daily_sessions(session_date)
        summary = {"sessions": len(sessions), "completed": 0, "pending": 0,
                   "total_minutes": 0, "completed_minutes": 0}
        for session in sessions:
            summary["total_minutes"] += session["allocated_duration"]
            if session["is_completed"]:
                summary["completed"] += 1
                summary["completed_minutes"] += session["allocated_duration"]
            else:
                summary["pending"] += 1
        return summary

    # ------------------------------------------------------------------
    # Updating
    # ------------------------------------------------------------------
    def _find_session(self, session_id):
        for session in database.get_sessions():
            if session["session_id"] == session_id:
                return session
        raise DatabaseError("Session not found.")

    def complete_session(self, session_id, complete_topic=True):
        """
        Mark a session completed.
        A session covers a WHOLE topic (topics are never split), so by default
        its topic is marked completed too.
        """
        session = self._find_session(session_id)
        database.set_session_status(session_id, "Completed")
        if complete_topic:
            database.set_topic_status(session["topic_id"], "Completed")

    def reopen_session(self, session_id, reopen_topic=True):
        """Mark a session pending again (and its topic, by default)."""
        session = self._find_session(session_id)
        database.set_session_status(session_id, "Pending")
        if reopen_topic:
            database.set_topic_status(session["topic_id"], "Pending")

    def delete_session(self, session_id):
        self._find_session(session_id)  # clear error if it does not exist
        database.delete_session(session_id)


# ----------------------------------------------------------------------
# Demo: run with   python -m modules.schedule_manager
# (uses a temporary database, so your real data is not touched)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import shutil
    import tempfile

    from modules.study_planner import StudyPlanner

    folder = tempfile.mkdtemp()
    database.DB_PATH = os.path.join(folder, "demo.db")
    database.init_db()

    dsa = database.add_subject("Data Structures", "CSE201")
    dbms = database.add_subject("DBMS", "CSE301")
    database.add_topic(dsa, "Arrays", 30, "High", "2026-12-02")
    database.add_topic(dsa, "Trees", 60, "High", "2026-12-05")
    database.add_topic(dbms, "SQL", 45, "Medium", "2026-12-01")
    database.add_topic(dbms, "Joins", 50, "High", "2026-12-03")

    planner = StudyPlanner()
    schedule = ScheduleManager()
    today = date(2026, 12, 1)
    day = "2026-12-01"

    def show(sessions):
        if not sessions:
            print("   (none)")
        for s in sessions:
            print("  ", str(s["session_id"]).rjust(2), s["session_date"], s["time_label"].ljust(13),
                  s["topic_name"].ljust(7), s["subject_name"].ljust(16),
                  str(s["allocated_duration"]).rjust(3), "min", s["status"])

    print("--- Save a timed plan (09:00) ---")
    plan = planner.generate_plan(120, start_time="09:00", today=today)
    print("Saved sessions:", schedule.save_plan(plan, day))
    show(schedule.get_daily_sessions(day))

    print("\n--- Complete the first session (its topic becomes completed too) ---")
    first = schedule.get_daily_sessions(day)[0]
    schedule.complete_session(first["session_id"])
    print("Topic status:", database.get_topic(first["topic_id"])["status"])
    print("Pending sessions:")
    show(schedule.get_pending_sessions())
    print("Day summary:", schedule.day_summary(day))

    print("\n--- Regenerate: pending sessions are replaced, completed one is kept ---")
    busy = schedule.busy_slots_for_date(day)
    print("Busy slots:", [(b["start_time"], b["end_time"]) for b in busy])
    plan = planner.generate_plan(120, start_time="09:00", busy_slots=busy, today=today)
    print("Saved sessions:", schedule.save_plan(plan, day))
    show(schedule.get_daily_sessions(day))

    print("\n--- Overlap is refused (plan ignores the completed 09:00 session) ---")
    clashing_plan = planner.generate_plan(120, start_time="09:15", today=today)
    try:
        schedule.save_plan(clashing_plan, day)
    except DatabaseError as error:
        print("Rejected:", error)
    print("Sessions unchanged:", len(schedule.get_daily_sessions(day)))

    print("\n--- A plan without a start time: no clock times are invented ---")
    plain = planner.generate_plan(90, today=today)
    print("Saved sessions:", schedule.save_plan(plain, "2026-12-02"))
    show(schedule.get_daily_sessions("2026-12-02"))
    print("Dates with sessions:", schedule.list_session_dates())

    print("\n--- Reopen, delete, invalid input ---")
    schedule.reopen_session(first["session_id"])
    print("Topic status after reopen:", database.get_topic(first["topic_id"])["status"])
    schedule.delete_session(first["session_id"])
    print("Sessions left on", day + ":", len(schedule.get_daily_sessions(day)))
    for action in [lambda: schedule.get_daily_sessions("01-12-2026"),
                   lambda: schedule.save_plan(plain, ""),
                   lambda: schedule.save_plan({"selected": []}, day),
                   lambda: schedule.complete_session(999)]:
        try:
            action()
        except DatabaseError as error:
            print("Rejected:", error)

    print("\n--- find_overlaps ---")
    sample = [{"topic_name": "A", "start_time": "09:00", "end_time": "10:00"},
              {"topic_name": "B", "start_time": "10:00", "end_time": "11:00"},
              {"topic_name": "C", "start_time": "10:30", "end_time": "11:30"},
              {"topic_name": "D", "start_time": None, "end_time": None}]
    for a, b in schedule.find_overlaps(sample):
        print("Overlap:", a["topic_name"], "and", b["topic_name"])

    shutil.rmtree(folder, ignore_errors=True)