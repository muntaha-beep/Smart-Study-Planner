"""
progress_tracker.py - progress numbers for the Progress page and the Dashboard
(Phase 4).

Every number is calculated from the real records in the database each time it
is asked for. Nothing is hard-coded, and an empty database gives zeros
(never a crash or a divide-by-zero).
"""

from datetime import date

import database
from algorithms.merge_sort import merge_sort_topics
from modules.topic_manager import TopicManager
from modules.schedule_manager import ScheduleManager


def percent(part, total):
    """part as a percentage of total, rounded to 1 decimal. 0.0 if total is 0."""
    if total == 0:
        return 0.0
    return round(part * 100 / total, 1)


def format_minutes(minutes):
    """90 -> '1h 30m', 45 -> '45m', 120 -> '2h', 0 -> '0m'."""
    hours = minutes // 60
    rest = minutes % 60
    if hours == 0:
        return str(rest) + "m"
    if rest == 0:
        return str(hours) + "h"
    return str(hours) + "h " + str(rest) + "m"


class ProgressTracker:
    """Calculate progress and dashboard statistics."""

    def __init__(self):
        self.topic_manager = TopicManager()
        self.schedule_manager = ScheduleManager()

    # ------------------------------------------------------------------
    # Overall progress
    # ------------------------------------------------------------------
    def overall_progress(self):
        """
        Totals for the whole application:
          total_topics, completed_topics, pending_topics, completion_percent
          total_minutes     : estimated time of ALL topics
          completed_minutes : estimated time of COMPLETED topics
          pending_minutes   : estimated time of PENDING topics
          total_sessions, completed_sessions, pending_sessions
          studied_minutes   : time of COMPLETED sessions (the study time done)
        """
        topics = database.get_topics()
        sessions = database.get_sessions()

        completed_topics = 0
        completed_minutes = 0
        total_minutes = 0
        for topic in topics:
            total_minutes += topic["estimated_duration"]
            if topic["status"] == "Completed":
                completed_topics += 1
                completed_minutes += topic["estimated_duration"]

        completed_sessions = 0
        studied_minutes = 0
        for session in sessions:
            if session["status"] == "Completed":
                completed_sessions += 1
                studied_minutes += session["allocated_duration"]

        return {
            "total_topics": len(topics),
            "completed_topics": completed_topics,
            "pending_topics": len(topics) - completed_topics,
            "completion_percent": percent(completed_topics, len(topics)),
            "total_minutes": total_minutes,
            "completed_minutes": completed_minutes,
            "pending_minutes": total_minutes - completed_minutes,
            "total_sessions": len(sessions),
            "completed_sessions": completed_sessions,
            "pending_sessions": len(sessions) - completed_sessions,
            "studied_minutes": studied_minutes,
        }

    # ------------------------------------------------------------------
    # Subject-wise progress
    # ------------------------------------------------------------------
    def subject_progress(self):
        """
        One row per subject (A-Z), including subjects with no topics yet:
          subject_id, subject_name, course_code, total_topics, completed_topics,
          pending_topics, percent, total_minutes, completed_minutes
        """
        topics = database.get_topics()
        rows = []
        for subject in database.get_all_subjects():
            total = 0
            done = 0
            total_minutes = 0
            done_minutes = 0
            for topic in topics:
                if topic["subject_id"] != subject["subject_id"]:
                    continue
                total += 1
                total_minutes += topic["estimated_duration"]
                if topic["status"] == "Completed":
                    done += 1
                    done_minutes += topic["estimated_duration"]
            rows.append({
                "subject_id": subject["subject_id"],
                "subject_name": subject["subject_name"],
                "course_code": subject["course_code"],
                "total_topics": total,
                "completed_topics": done,
                "pending_topics": total - done,
                "percent": percent(done, total),
                "total_minutes": total_minutes,
                "completed_minutes": done_minutes,
            })
        return rows

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def upcoming_deadlines(self, limit=5, today=None):
        """
        Pending topics that have a deadline, earliest first (overdue ones come
        first). Each topic gets "days_left" (negative = late) and "overdue".
        """
        today = today or date.today()
        with_deadline = []
        for topic in database.get_topics(status="Pending"):
            if topic["deadline"]:
                with_deadline.append(topic)

        ordered = merge_sort_topics(with_deadline, "deadline")  # our own sort
        result = []
        for topic in ordered[:limit]:
            row = dict(topic)
            row["days_left"] = self.topic_manager.days_until_deadline(topic, today)
            row["overdue"] = self.topic_manager.is_overdue(topic, today)
            result.append(row)
        return result

    def dashboard_stats(self, today=None, deadline_limit=5):
        """Everything the Dashboard shows, in one dictionary."""
        today = today or date.today()
        overall = self.overall_progress()
        today_text = today.strftime("%Y-%m-%d")
        return {
            "total_subjects": len(database.get_all_subjects()),
            "total_topics": overall["total_topics"],
            "completed_topics": overall["completed_topics"],
            "pending_topics": overall["pending_topics"],
            "total_estimated_minutes": overall["total_minutes"],
            "total_estimated_hours": round(overall["total_minutes"] / 60, 1),
            "overall_percent": overall["completion_percent"],
            "upcoming_deadlines": self.upcoming_deadlines(deadline_limit, today),
            "todays_sessions": self.schedule_manager.get_daily_sessions(today_text),
        }


# ----------------------------------------------------------------------
# Demo: run with   python -m modules.progress_tracker
# (uses a temporary database, so your real data is not touched)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import shutil
    import tempfile

    folder = tempfile.mkdtemp()
    database.DB_PATH = os.path.join(folder, "demo.db")
    database.init_db()
    tracker = ProgressTracker()
    today = date(2026, 12, 1)

    print("=== Empty database (must not crash) ===")
    print(tracker.overall_progress())
    print(tracker.subject_progress())
    stats = tracker.dashboard_stats(today)
    print(stats["total_subjects"], stats["overall_percent"], stats["upcoming_deadlines"],
          stats["todays_sessions"])

    dsa = database.add_subject("Data Structures", "CSE201")
    dbms = database.add_subject("DBMS", "CSE301")
    database.add_subject("Operating Systems", "CSE401")  # no topics yet
    arrays = database.add_topic(dsa, "Arrays", 30, "High", "2026-12-02")
    database.add_topic(dsa, "Trees", 60, "High", "2026-12-05")
    database.add_topic(dsa, "Graphs", 50, "Medium", "2026-12-20")
    sql = database.add_topic(dbms, "SQL", 45, "Medium", "2026-12-01")
    joins = database.add_topic(dbms, "Joins", 50, "High", "2026-12-03")
    database.add_topic(dbms, "Normalization", 35, "Low", "2026-11-28")
    database.add_topic(dbms, "Indexes", 40, "Low")  # no deadline
    database.set_topic_status(arrays, "Completed")

    s1 = database.add_session(arrays, 30, "2026-12-01", "09:00", "09:30")
    database.add_session(sql, 45, "2026-12-01", "09:30", "10:15")
    database.add_session(joins, 50, "2026-12-02")
    database.set_session_status(s1, "Completed")

    print("\n=== Overall progress ===")
    overall = tracker.overall_progress()
    for key in overall:
        print(" ", key.ljust(20), overall[key])
    print("  studied time        ", format_minutes(overall["studied_minutes"]))

    print("\n=== Subject-wise progress ===")
    for row in tracker.subject_progress():
        print(" ", row["subject_name"].ljust(18), str(row["completed_topics"]) + "/"
              + str(row["total_topics"]), "topics ", str(row["percent"]).rjust(5) + "%",
              format_minutes(row["completed_minutes"]) + " of " + format_minutes(row["total_minutes"]))

    print("\n=== Dashboard (pretend today is 2026-12-01) ===")
    stats = tracker.dashboard_stats(today)
    print("  Subjects:", stats["total_subjects"], "| Topics:", stats["total_topics"],
          "| Completed:", stats["completed_topics"], "| Pending:", stats["pending_topics"])
    print("  Estimated study time:", stats["total_estimated_hours"], "hours",
          "| Overall progress:", stats["overall_percent"], "%")
    print("  Upcoming deadlines:")
    for t in stats["upcoming_deadlines"]:
        flag = "OVERDUE" if t["overdue"] else "in " + str(t["days_left"]) + " day(s)"
        print("    ", t["topic_name"].ljust(14), t["deadline"], flag)
    print("  Today's sessions:")
    for s in stats["todays_sessions"]:
        print("    ", s["time_label"].ljust(12), s["topic_name"].ljust(7), s["status"])

    print("\n=== Helpers ===")
    print([format_minutes(m) for m in (0, 45, 60, 90, 135)])
    print(percent(1, 3), percent(0, 0), percent(5, 5))

    shutil.rmtree(folder, ignore_errors=True)