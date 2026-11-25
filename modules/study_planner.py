"""
study_planner.py - the Smart Study Plan Generator (Phase 4).

How a plan is made (each step uses one of our own algorithms):

  Step 1  Load all PENDING topics from the database (completed ones are left out).
  Step 2  Give every topic an importance VALUE:
              value = priority points + deadline urgency bonus
              priority points : High = 5, Medium = 3, Low = 1
              urgency bonus   : overdue or due today = +3
                                due in 1-3 days      = +2
                                due in 4-7 days      = +1
                                later / no deadline  = +0
          (You can switch the urgency bonus off; then value = priority points.)
  Step 3  SORT the topics with the chosen sorting algorithm and criterion.
          A stable Merge Sort first sets the tie-break order (High priority first,
          or earlier deadline first when sorting by priority). Merge and Insertion
          Sort keep that tie order; Quick and Heap Sort are not stable and may not.
  Step 4  0/1 KNAPSACK picks COMPLETE topics that give the largest total value
          without going over the available minutes.
          The sorted order of the chosen topics is the suggested study order.
  Step 5  (only if a start time is given) place the chosen topics one after
          another from that time, jumping over any busy slots, then run
          ACTIVITY SELECTION as an overlap check on the finished sessions.

A topic is never shortened: its allocated time equals its estimated time.
If no start time is given, NO clock times are invented.
"""

from datetime import date

from database import DatabaseError, validate_time
from algorithms import PRIORITY_VALUE
from algorithms.merge_sort import merge_sort, merge_sort_topics
from algorithms.zero_one_knapsack import zero_one_knapsack
from algorithms.activity_selection import (
    activity_selection, time_to_minutes, minutes_to_time)
from modules.topic_manager import TopicManager, SORT_ALGORITHMS, SORT_CRITERIA

MAX_AVAILABLE_MINUTES = 1440  # one day


class StudyPlanner:
    """Generate a study plan for the available time."""

    def __init__(self):
        self.topic_manager = TopicManager()

    # ------------------------------------------------------------------
    # Input helpers
    # ------------------------------------------------------------------
    def parse_available_time(self, amount, unit="minutes"):
        """
        Turn what the user typed into whole minutes.
        amount: text or number, e.g. "90" or "1.5"; unit: "minutes" or "hours".
        """
        try:
            number = float(str(amount).strip())
        except ValueError:
            raise DatabaseError("Available time must be a number.")
        if number <= 0:
            raise DatabaseError("Available time must be greater than zero.")

        unit = str(unit).strip().lower()
        if unit.startswith("hour"):
            minutes = number * 60
        elif unit.startswith("min"):
            minutes = number
        else:
            raise DatabaseError("Unit must be minutes or hours.")

        if abs(minutes - round(minutes)) > 1e-9:
            raise DatabaseError("Time must be a whole number of minutes "
                                "(for example 1.5 hours = 90 minutes).")
        minutes = int(round(minutes))
        if minutes > MAX_AVAILABLE_MINUTES:
            raise DatabaseError("Available time cannot be more than "
                                + str(MAX_AVAILABLE_MINUTES) + " minutes (one day).")
        return minutes

    # ------------------------------------------------------------------
    # Importance value
    # ------------------------------------------------------------------
    def urgency_bonus(self, days_left):
        """Extra importance for topics whose deadline is close."""
        if days_left is None:
            return 0
        if days_left <= 0:
            return 3
        if days_left <= 3:
            return 2
        if days_left <= 7:
            return 1
        return 0

    def importance(self, topic, today, use_deadline_urgency=True):
        """Return (total value, priority points, urgency bonus) for a topic."""
        points = PRIORITY_VALUE[topic["priority"]]
        bonus = 0
        if use_deadline_urgency:
            bonus = self.urgency_bonus(self.topic_manager.days_until_deadline(topic, today))
        return points + bonus, points, bonus

    # ------------------------------------------------------------------
    # Placing sessions on the clock
    # ------------------------------------------------------------------
    def _read_busy_slots(self, busy_slots):
        """Convert busy slots (dicts with start_time/end_time as 'HH:MM') to minutes."""
        busy = []
        for slot in busy_slots or []:
            if not slot.get("start_time") or not slot.get("end_time"):
                continue  # a slot without clock times cannot block anything
            start = time_to_minutes(slot["start_time"])
            finish = time_to_minutes(slot["end_time"])
            if finish > start:
                busy.append({"start": start, "finish": finish})
        return merge_sort(busy, key=lambda slot: slot["start"])

    def _place_sessions(self, selected, start_minute, busy, warnings):
        """Give every selected topic a start and end time (back to back)."""
        cursor = start_minute
        for topic in selected:
            duration = topic["allocated_duration"]

            # Jump forward while the slot [cursor, cursor + duration) hits a busy slot.
            moved = True
            while moved:
                moved = False
                for slot in busy:
                    if slot["start"] < cursor + duration and slot["finish"] > cursor:
                        cursor = slot["finish"]
                        moved = True

            if cursor + duration > 24 * 60:
                topic["start_time"] = None
                topic["end_time"] = None
                warnings.append("'" + topic["topic_name"] + "' does not fit before midnight "
                                "from the chosen start time, so it has no clock time.")
                continue

            topic["start_time"] = minutes_to_time(cursor)
            topic["end_time"] = minutes_to_time(cursor + duration)
            cursor += duration

    # ------------------------------------------------------------------
    # The plan generator
    # ------------------------------------------------------------------
    def generate_plan(self, available_minutes, sort_by="Deadline", algorithm="Merge Sort",
                      start_time="", busy_slots=None, subject_id=None,
                      use_deadline_urgency=True, today=None):
        """
        Build a study plan and return it as a dictionary.

        available_minutes    : whole minutes the student can study (1..1440)
        sort_by              : "Deadline", "Priority", "Duration" or "Name"
        algorithm            : "Merge Sort", "Insertion Sort", "Quick Sort", "Heap Sort"
        start_time           : "HH:MM" to get clock times, or "" for none
        busy_slots           : optional list of {"start_time", "end_time"} to avoid
        subject_id           : plan only this subject (None = all subjects)
        use_deadline_urgency : add the urgency bonus to the importance value
        today                : a date (only for testing); default is today

        The returned dictionary has:
          "available_minutes", "total_allocated", "remaining", "total_value"
          "selected"     : topics in suggested study order. Each has
                           "order", "estimated_duration", "allocated_duration",
                           "importance_value", "priority_points", "urgency_bonus",
                           "start_time", "end_time" (None if no clock times)
          "not_selected" : topics left out, each with a "reason"
          "explanation"  : list of text lines saying which algorithm was used and why
          "warnings"     : list of problems (for example a topic past midnight)
          "knapsack"     : the full 0/1 Knapsack result (DP table included)
        """
        # ---- check the inputs ----
        if not isinstance(available_minutes, int) or available_minutes <= 0:
            raise DatabaseError("Available time must be a whole number of minutes above zero.")
        if available_minutes > MAX_AVAILABLE_MINUTES:
            raise DatabaseError("Available time cannot be more than "
                                + str(MAX_AVAILABLE_MINUTES) + " minutes (one day).")
        if sort_by not in SORT_CRITERIA:
            raise DatabaseError("Cannot sort by: " + str(sort_by))
        if algorithm not in SORT_ALGORITHMS:
            raise DatabaseError("Unknown sorting algorithm: " + str(algorithm))
        start_time = validate_time(start_time)  # 'HH:MM' or None
        today = today or date.today()

        explanation = []
        warnings = []

        # ---- Step 1: pending topics only ----
        pending = self.topic_manager.list_topics(subject_id=subject_id, status="Pending")
        explanation.append("Step 1: loaded " + str(len(pending)) + " pending topic(s) from the "
                           "database. Completed topics are not planned.")

        if len(pending) == 0:
            warnings.append("There are no pending topics to plan.")
            return {
                "available_minutes": available_minutes, "total_allocated": 0,
                "remaining": available_minutes, "total_value": 0,
                "selected": [], "not_selected": [], "explanation": explanation,
                "warnings": warnings, "knapsack": None,
            }

        # ---- Step 2: importance value ----
        topics = []
        for topic in pending:
            row = dict(topic)
            value, points, bonus = self.importance(row, today, use_deadline_urgency)
            row["importance_value"] = value
            row["priority_points"] = points
            row["urgency_bonus"] = bonus
            topics.append(row)
        if use_deadline_urgency:
            explanation.append("Step 2: importance value = priority points (High 5, Medium 3, "
                               "Low 1) + deadline bonus (due today/overdue +3, within 3 days +2, "
                               "within 7 days +1).")
        else:
            explanation.append("Step 2: importance value = priority points "
                               "(High 5, Medium 3, Low 1). Deadlines are not used.")

        # ---- Step 3: sort with our own algorithm ----
        # First a tie-break order (stable Merge Sort), then the chosen sort on top.
        if SORT_CRITERIA[sort_by] == "priority":
            topics = merge_sort_topics(topics, "deadline")  # ties: earlier deadline first
            tie_text = "equal items: earlier deadline first"
        else:
            topics = merge_sort_topics(topics, "priority")  # ties: High priority first
            tie_text = "equal items: higher priority first"
        topics = SORT_ALGORITHMS[algorithm](topics, SORT_CRITERIA[sort_by])
        step3 = ("Step 3: sorted by " + sort_by.lower() + " using " + algorithm
                 + " (" + tie_text + ").")
        if algorithm in ("Quick Sort", "Heap Sort"):
            step3 += " This algorithm is not stable, so equal items may change order."
        explanation.append(step3)

        # ---- Step 4: 0/1 Knapsack ----
        items = []
        for topic in topics:
            items.append({"name": topic["topic_name"], "value": topic["importance_value"],
                          "weight": topic["estimated_duration"], "topic_id": topic["topic_id"]})
        knapsack = zero_one_knapsack(items, available_minutes)

        by_id = {}
        for topic in topics:
            by_id[topic["topic_id"]] = topic

        selected = []
        for item in knapsack["selected"]:  # already in the sorted (study) order
            topic = dict(by_id[item["topic_id"]])
            topic["order"] = len(selected) + 1
            topic["allocated_duration"] = topic["estimated_duration"]  # never shortened
            topic["start_time"] = None
            topic["end_time"] = None
            selected.append(topic)

        not_selected = []
        for item in knapsack["rejected"]:
            topic = dict(by_id[item["topic_id"]])
            topic["allocated_duration"] = 0
            topic["reason"] = "Not selected: " + item["reason"]
            not_selected.append(topic)

        total_allocated = knapsack["total_weight"]
        explanation.append("Step 4: 0/1 Knapsack chose " + str(len(selected)) + " complete topic(s) "
                           "with total importance " + str(knapsack["total_value"]) + ", using "
                           + str(total_allocated) + " of " + str(available_minutes)
                           + " minutes. A topic is taken completely or not at all.")

        # ---- Step 5: clock times + Activity Selection overlap check ----
        if start_time and selected:
            busy = self._read_busy_slots(busy_slots)
            self._place_sessions(selected, time_to_minutes(start_time), busy, warnings)

            sessions = []
            for topic in selected:
                if topic["start_time"]:
                    sessions.append({"name": str(topic["order"]) + ". " + topic["topic_name"],
                                     "start": time_to_minutes(topic["start_time"]),
                                     "finish": time_to_minutes(topic["end_time"])})
            chosen, clashing = activity_selection(sessions)
            if clashing:
                warnings.append("Activity Selection found overlapping sessions: "
                                + ", ".join(s["name"] for s in clashing))
            explanation.append("Step 5: sessions placed from " + start_time
                               + (", skipping " + str(len(busy)) + " busy slot(s)" if busy else "")
                               + ". Activity Selection check: " + str(len(chosen)) + " of "
                               + str(len(sessions)) + " sessions are compatible (no overlap).")
        elif selected:
            explanation.append("Step 5: no start time given, so no clock times were created. "
                               "Sessions are shown in order with their durations.")

        if len(selected) == 0:
            warnings.append("No topic fits into " + str(available_minutes)
                            + " minutes. Try more time or shorter topics.")

        return {
            "available_minutes": available_minutes,
            "total_allocated": total_allocated,
            "remaining": available_minutes - total_allocated,
            "total_value": knapsack["total_value"],
            "selected": selected,
            "not_selected": not_selected,
            "explanation": explanation,
            "warnings": warnings,
            "knapsack": knapsack,
        }

    # ------------------------------------------------------------------
    # Text version of a plan (used by the demo and handy for debugging)
    # ------------------------------------------------------------------
    def format_plan(self, plan):
        lines = []
        for step in plan["explanation"]:
            lines.append(step)
        lines.append("")
        lines.append("SUGGESTED STUDY ORDER")
        if not plan["selected"]:
            lines.append("   (nothing selected)")
        for t in plan["selected"]:
            clock = ""
            if t["start_time"]:
                clock = "  " + t["start_time"] + "-" + t["end_time"]
            lines.append("   " + str(t["order"]) + ". " + t["topic_name"] + " [" + t["subject_name"]
                         + "] " + t["priority"] + ", value " + str(t["importance_value"])
                         + ", estimated " + str(t["estimated_duration"]) + " min, allocated "
                         + str(t["allocated_duration"]) + " min, deadline "
                         + str(t["deadline"]) + clock)
        if plan["not_selected"]:
            lines.append("NOT SELECTED")
            for t in plan["not_selected"]:
                lines.append("   - " + t["topic_name"] + " (" + str(t["estimated_duration"])
                             + " min, value " + str(t["importance_value"]) + "): " + t["reason"])
        lines.append("")
        lines.append("Total allocated: " + str(plan["total_allocated"]) + " min | Remaining: "
                     + str(plan["remaining"]) + " min | Total value: " + str(plan["total_value"]))
        for warning in plan["warnings"]:
            lines.append("WARNING: " + warning)
        return "\n".join(lines)


# ----------------------------------------------------------------------
# Demo: run with   python -m modules.study_planner
# (uses a temporary database, so your real data is not touched)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import shutil
    import tempfile

    import database

    folder = tempfile.mkdtemp()
    database.DB_PATH = os.path.join(folder, "demo.db")
    database.init_db()

    dsa = database.add_subject("Data Structures", "CSE201")
    dbms = database.add_subject("DBMS", "CSE301")
    database.add_topic(dsa, "Arrays", 30, "High", "2026-12-02")
    database.add_topic(dsa, "Trees", 60, "High", "2026-12-05")
    database.add_topic(dsa, "Graphs", 50, "Medium", "2026-12-20")
    database.add_topic(dsa, "Sorting", 40, "Low")
    database.add_topic(dbms, "SQL", 45, "Medium", "2026-12-01")
    database.add_topic(dbms, "Joins", 50, "High", "2026-12-03")
    database.add_topic(dbms, "Normalization", 35, "Low", "2026-11-28")
    done = database.add_topic(dbms, "Intro", 20, "High")
    database.set_topic_status(done, "Completed")

    planner = StudyPlanner()
    today = date(2026, 12, 1)  # fixed, so the demo output never changes

    print("=== Plan 1: 120 minutes, sorted by deadline, no start time ===")
    plan = planner.generate_plan(120, today=today)
    print(planner.format_plan(plan))

    print("\n=== Plan 2: 2 hours from 09:00 with a busy slot 10:00-10:30 ===")
    minutes = planner.parse_available_time("2", "hours")
    plan = planner.generate_plan(minutes, sort_by="Priority", algorithm="Heap Sort",
                                 start_time="09:00", today=today,
                                 busy_slots=[{"start_time": "10:00", "end_time": "10:30"}])
    print(planner.format_plan(plan))

    print("\n=== Plan 3: only 20 minutes (nothing fits) ===")
    print(planner.format_plan(planner.generate_plan(20, today=today)))

    print("\n=== Plan 4: deadlines switched off ===")
    plan = planner.generate_plan(120, today=today, use_deadline_urgency=False)
    print("Chosen:", [t["topic_name"] for t in plan["selected"]], "| value", plan["total_value"])

    print("\n=== Plan 5: no pending topics ===")
    for topic in database.get_topics():
        database.set_topic_status(topic["topic_id"], "Completed")
    print(planner.format_plan(planner.generate_plan(60, today=today)))

    print("\n=== Invalid input ===")
    for text, unit in [("abc", "minutes"), ("0", "minutes"), ("-5", "hours"),
                       ("1.234", "hours"), ("5", "days"), ("2000", "minutes")]:
        try:
            planner.parse_available_time(text, unit)
        except DatabaseError as error:
            print("Rejected", repr(text), unit + ":", error)
    for kwargs in [{"available_minutes": 0}, {"available_minutes": 60, "sort_by": "Color"},
                   {"available_minutes": 60, "algorithm": "Bogo Sort"},
                   {"available_minutes": 60, "start_time": "9am"}]:
        try:
            planner.generate_plan(**kwargs)
        except DatabaseError as error:
            print("Rejected", kwargs, "->", error)

    shutil.rmtree(folder, ignore_errors=True)