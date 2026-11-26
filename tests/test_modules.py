"""
Tests for the five backend modules:
  subject_manager, topic_manager, study_planner, schedule_manager, progress_tracker

Run from the project root:   python -m unittest tests.test_modules -v

Every test uses its own temporary database, so your real study_planner.db is
never touched.
"""

import itertools
import os
import random
import shutil
import tempfile
import unittest
from datetime import date

import database
from database import DatabaseError
from modules.subject_manager import SubjectManager
from modules.topic_manager import TopicManager
from modules.study_planner import StudyPlanner
from modules.schedule_manager import ScheduleManager
from modules.progress_tracker import ProgressTracker, percent, format_minutes

TODAY = date(2026, 12, 1)  # fixed "today" so deadline maths never changes


class BaseTest(unittest.TestCase):
    """Gives every test a fresh temporary database and the five managers."""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        database.DB_PATH = os.path.join(self.folder, "test.db")
        database.init_db()
        self.subjects = SubjectManager()
        self.topics = TopicManager()
        self.planner = StudyPlanner()
        self.schedule = ScheduleManager()
        self.progress = ProgressTracker()

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def names(self, topics):
        return [t["topic_name"] for t in topics]

    def add_sample_topics(self):
        """Two subjects and seven pending topics (same data as the demos)."""
        self.dsa = self.subjects.add_subject("Data Structures", "CSE201")
        self.dbms = self.subjects.add_subject("DBMS", "CSE301")
        self.topics.add_topic(self.dsa, "Arrays", 30, "High", "2026-12-02")
        self.topics.add_topic(self.dsa, "Trees", 60, "High", "2026-12-05")
        self.topics.add_topic(self.dsa, "Graphs", 50, "Medium", "2026-12-20")
        self.topics.add_topic(self.dsa, "Sorting", 40, "Low")
        self.topics.add_topic(self.dbms, "SQL", 45, "Medium", "2026-12-01")
        self.topics.add_topic(self.dbms, "Joins", 50, "High", "2026-12-03")
        self.topics.add_topic(self.dbms, "Normalization", 35, "Low", "2026-11-28")


# ======================================================================
# Subject manager
# ======================================================================
class TestSubjectManager(BaseTest):
    def test_add_get_and_list(self):
        sid = self.subjects.add_subject("  Operating Systems  ", " CSE401 ", " Processes ")
        subject = self.subjects.get_subject(sid)
        self.assertEqual(subject["subject_name"], "Operating Systems")  # spaces trimmed
        self.assertEqual(subject["course_code"], "CSE401")
        self.assertEqual(len(self.subjects.list_subjects()), 1)

    def test_optional_fields_can_be_empty(self):
        self.subjects.add_subject("Networks")
        self.subjects.add_subject("Software Engineering")
        self.assertEqual(len(self.subjects.list_subjects()), 2)

    def test_duplicates_rejected(self):
        self.subjects.add_subject("DBMS", "CSE301")
        with self.assertRaises(DatabaseError):
            self.subjects.add_subject("dbms")
        with self.assertRaises(DatabaseError):
            self.subjects.add_subject("Other", "cse301")

    def test_invalid_input_rejected(self):
        for args in [("",), ("   ",), ("A" * 101,), ("Name", "X" * 21), ("Name", "", "D" * 301)]:
            with self.subTest(args=args):
                with self.assertRaises(DatabaseError):
                    self.subjects.add_subject(*args)
        self.assertEqual(self.subjects.list_subjects(), [])

    def test_search(self):
        self.subjects.add_subject("Computer Networks", "CSE401")
        self.subjects.add_subject("Software Engineering", "CSE305")
        self.assertEqual(len(self.subjects.list_subjects("network")), 1)
        self.assertEqual(len(self.subjects.list_subjects("CSE3")), 1)
        self.assertEqual(self.subjects.list_subjects("zzz"), [])
        self.assertEqual(len(self.subjects.list_subjects("   ")), 2)  # blank = all

    def test_update(self):
        sid = self.subjects.add_subject("Old")
        self.subjects.update_subject(sid, "New", "N1", "text")
        self.assertEqual(self.subjects.get_subject(sid)["subject_name"], "New")
        with self.assertRaises(DatabaseError):
            self.subjects.update_subject(sid, "")
        with self.assertRaises(DatabaseError):
            self.subjects.update_subject(999, "Ghost")

    def test_get_missing_subject(self):
        with self.assertRaises(DatabaseError):
            self.subjects.get_subject(999)

    def test_counts_and_delete(self):
        sid = self.subjects.add_subject("DSA")
        t1 = self.topics.add_topic(sid, "Arrays", 30, "High")
        self.topics.add_topic(sid, "Trees", 40, "Low")
        self.topics.mark_completed(t1)
        row = self.subjects.list_subjects_with_counts()[0]
        self.assertEqual(row["topic_count"], 2)
        self.assertEqual(row["completed_count"], 1)
        self.assertEqual(self.subjects.delete_subject(sid), 2)
        self.assertEqual(self.topics.list_topics(), [])
        with self.assertRaises(DatabaseError):
            self.subjects.delete_subject(sid)


# ======================================================================
# Topic manager
# ======================================================================
class TestTopicManager(BaseTest):
    def setUp(self):
        super().setUp()
        self.sid = self.subjects.add_subject("DSA")

    def test_add_normalises_priority_and_trims(self):
        tid = self.topics.add_topic(self.sid, "  Trees ", "60", "high", "2026-12-05")
        topic = self.topics.get_topic(tid)
        self.assertEqual(topic["topic_name"], "Trees")
        self.assertEqual(topic["priority"], "High")
        self.assertEqual(topic["estimated_duration"], 60)
        self.assertEqual(topic["status"], "Pending")
        self.assertEqual(topic["subject_name"], "DSA")

    def test_invalid_input_rejected(self):
        bad = [
            (self.sid, "", 30, "High", ""),
            (self.sid, "X", 0, "High", ""),
            (self.sid, "X", -5, "High", ""),
            (self.sid, "X", "abc", "High", ""),
            (self.sid, "X", 30.5, "High", ""),
            (self.sid, "X", 1441, "High", ""),
            (self.sid, "X", 30, "Urgent", ""),
            (self.sid, "X", 30, "", ""),
            (self.sid, "X", 30, "High", "05-12-2026"),
            (self.sid, "X", 30, "High", "2026-02-30"),
            (self.sid, "N" * 101, 30, "High", ""),
            (999, "X", 30, "High", ""),
        ]
        for args in bad:
            with self.subTest(args=args):
                with self.assertRaises(DatabaseError):
                    self.topics.add_topic(*args)
        self.assertEqual(self.topics.list_topics(), [])

    def test_boundary_durations_accepted(self):
        self.topics.add_topic(self.sid, "One minute", 1, "Low")
        self.topics.add_topic(self.sid, "A whole day", 1440, "Low")
        self.assertEqual(len(self.topics.list_topics()), 2)

    def test_duplicate_name_in_same_subject_rejected(self):
        self.topics.add_topic(self.sid, "Arrays", 30, "High")
        with self.assertRaises(DatabaseError):
            self.topics.add_topic(self.sid, "arrays", 20, "Low")

    def test_update_keeps_status(self):
        tid = self.topics.add_topic(self.sid, "Arrays", 30, "High")
        self.topics.mark_completed(tid)
        self.topics.update_topic(tid, self.sid, "Arrays 2", 45, "low", "2026-12-10")
        topic = self.topics.get_topic(tid)
        self.assertEqual(topic["topic_name"], "Arrays 2")
        self.assertEqual(topic["priority"], "Low")
        self.assertEqual(topic["status"], "Completed")
        with self.assertRaises(DatabaseError):
            self.topics.update_topic(999, self.sid, "Ghost", 30, "High")
        with self.assertRaises(DatabaseError):
            self.topics.update_topic(tid, self.sid, "Bad", 0, "High")

    def test_status_changes(self):
        tid = self.topics.add_topic(self.sid, "Arrays", 30, "High")
        self.topics.mark_completed(tid)
        self.assertEqual(self.topics.get_topic(tid)["status"], "Completed")
        self.topics.mark_pending(tid)
        self.assertEqual(self.topics.get_topic(tid)["status"], "Pending")
        self.assertEqual(self.topics.toggle_status(tid), "Completed")
        self.assertEqual(self.topics.toggle_status(tid), "Pending")
        with self.assertRaises(DatabaseError):
            self.topics.toggle_status(999)

    def test_filters_and_search(self):
        other = self.subjects.add_subject("DBMS")
        a = self.topics.add_topic(self.sid, "Arrays", 30, "High")
        self.topics.add_topic(self.sid, "Trees", 40, "Low")
        self.topics.add_topic(other, "SQL", 50, "High")
        self.topics.mark_completed(a)
        self.assertEqual(len(self.topics.list_topics(subject_id=self.sid)), 2)
        self.assertEqual(len(self.topics.list_topics(priority="High")), 2)
        self.assertEqual(len(self.topics.list_topics(status="Completed")), 1)
        self.assertEqual(len(self.topics.list_topics(status="Pending")), 2)
        self.assertEqual(self.names(self.topics.list_topics(keyword="sql")), ["SQL"])
        self.assertEqual(len(self.topics.list_topics(subject_id=self.sid, priority="High")), 1)
        self.assertEqual(self.topics.list_topics(keyword="nothing"), [])

    def test_sorting_with_every_algorithm(self):
        self.topics.add_topic(self.sid, "Trees", 60, "High", "2026-12-05")
        self.topics.add_topic(self.sid, "Arrays", 30, "Low")
        self.topics.add_topic(self.sid, "SQL", 45, "Medium", "2026-12-01")
        for algorithm in ["Merge Sort", "Insertion Sort", "Quick Sort", "Heap Sort"]:
            with self.subTest(algorithm=algorithm):
                by_duration = self.topics.list_topics(sort_by="Duration", algorithm=algorithm)
                self.assertEqual(self.names(by_duration), ["Arrays", "SQL", "Trees"])
                by_deadline = self.topics.list_topics(sort_by="Deadline", algorithm=algorithm)
                self.assertEqual(self.names(by_deadline), ["SQL", "Trees", "Arrays"])  # None last
                by_priority = self.topics.list_topics(sort_by="Priority", algorithm=algorithm)
                self.assertEqual(self.names(by_priority), ["Trees", "SQL", "Arrays"])
                by_name = self.topics.list_topics(sort_by="Name", algorithm=algorithm)
                self.assertEqual(self.names(by_name), ["Arrays", "SQL", "Trees"])

    def test_unknown_sort_options_rejected(self):
        with self.assertRaises(DatabaseError):
            self.topics.list_topics(sort_by="Color")
        with self.assertRaises(DatabaseError):
            self.topics.list_topics(sort_by="Name", algorithm="Bogo Sort")

    def test_sorting_empty_list(self):
        self.assertEqual(self.topics.list_topics(sort_by="Name"), [])

    def test_deadline_helpers(self):
        late = self.topics.get_topic(self.topics.add_topic(self.sid, "Late", 30, "High", "2026-11-30"))
        today = self.topics.get_topic(self.topics.add_topic(self.sid, "Today", 30, "High", "2026-12-01"))
        none = self.topics.get_topic(self.topics.add_topic(self.sid, "None", 30, "High"))
        self.assertEqual(self.topics.days_until_deadline(late, TODAY), -1)
        self.assertEqual(self.topics.days_until_deadline(today, TODAY), 0)
        self.assertIsNone(self.topics.days_until_deadline(none, TODAY))
        self.assertTrue(self.topics.is_overdue(late, TODAY))
        self.assertFalse(self.topics.is_overdue(today, TODAY))
        self.assertFalse(self.topics.is_overdue(none, TODAY))
        done = dict(late)
        done["status"] = "Completed"
        self.assertFalse(self.topics.is_overdue(done, TODAY))  # completed is never overdue

    def test_delete(self):
        tid = self.topics.add_topic(self.sid, "Arrays", 30, "High")
        self.topics.delete_topic(tid)
        with self.assertRaises(DatabaseError):
            self.topics.get_topic(tid)
        with self.assertRaises(DatabaseError):
            self.topics.delete_topic(tid)


# ======================================================================
# Study planner
# ======================================================================
class TestStudyPlanner(BaseTest):
    def test_parse_available_time(self):
        self.assertEqual(self.planner.parse_available_time("90"), 90)
        self.assertEqual(self.planner.parse_available_time("2", "hours"), 120)
        self.assertEqual(self.planner.parse_available_time("1.5", "Hours"), 90)
        self.assertEqual(self.planner.parse_available_time(45, "minutes"), 45)
        self.assertEqual(self.planner.parse_available_time("1440"), 1440)

    def test_parse_available_time_rejects_bad_input(self):
        for text, unit in [("abc", "minutes"), ("", "minutes"), ("0", "minutes"),
                           ("-5", "minutes"), ("1.234", "hours"), ("30.5", "minutes"),
                           ("5", "days"), ("1441", "minutes"), ("25", "hours")]:
            with self.subTest(text=text, unit=unit):
                with self.assertRaises(DatabaseError):
                    self.planner.parse_available_time(text, unit)

    def test_generate_plan_rejects_bad_input(self):
        for kwargs in [{"available_minutes": 0}, {"available_minutes": -5},
                       {"available_minutes": "60"}, {"available_minutes": 1441},
                       {"available_minutes": 60, "sort_by": "Color"},
                       {"available_minutes": 60, "algorithm": "Bogo Sort"},
                       {"available_minutes": 60, "start_time": "9am"}]:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(DatabaseError):
                    self.planner.generate_plan(**kwargs)

    def test_example_plan(self):
        self.add_sample_topics()
        plan = self.planner.generate_plan(120, today=TODAY)
        self.assertEqual(self.names(plan["selected"]), ["Normalization", "Arrays", "Joins"])
        self.assertEqual(plan["total_value"], 18)
        self.assertEqual(plan["total_allocated"], 115)
        self.assertEqual(plan["remaining"], 5)
        self.assertEqual([t["order"] for t in plan["selected"]], [1, 2, 3])

    def test_completed_topics_are_never_planned(self):
        self.add_sample_topics()
        done = self.topics.add_topic(self.dsa, "Intro", 10, "High", "2026-12-01")
        self.topics.mark_completed(done)
        plan = self.planner.generate_plan(1440, today=TODAY)
        everything = self.names(plan["selected"]) + self.names(plan["not_selected"])
        self.assertNotIn("Intro", everything)
        self.assertEqual(len(everything), 7)

    def test_never_exceeds_available_time_and_keeps_durations(self):
        self.add_sample_topics()
        for minutes in [1, 29, 30, 60, 99, 120, 200, 400, 1440]:
            with self.subTest(minutes=minutes):
                plan = self.planner.generate_plan(minutes, today=TODAY)
                self.assertLessEqual(plan["total_allocated"], minutes)
                self.assertEqual(plan["remaining"], minutes - plan["total_allocated"])
                for topic in plan["selected"]:
                    # estimated time is never silently changed
                    self.assertEqual(topic["allocated_duration"], topic["estimated_duration"])
                for topic in plan["not_selected"]:
                    self.assertEqual(topic["allocated_duration"], 0)
                    self.assertIn("reason", topic)
                self.assertEqual(len(plan["selected"]) + len(plan["not_selected"]), 7)

    def test_plan_matches_brute_force_best_value(self):
        generator = random.Random(11)
        for _ in range(60):
            for topic in self.topics.list_topics():
                self.topics.delete_topic(topic["topic_id"])
            sid = self.subjects.list_subjects()[0]["subject_id"] if self.subjects.list_subjects() \
                else self.subjects.add_subject("S")
            for i in range(generator.randint(1, 7)):
                deadline = generator.choice(["", "2026-11-28", "2026-12-02", "2026-12-06", "2026-12-30"])
                self.topics.add_topic(sid, "T" + str(i), generator.choice([15, 30, 45, 60, 90]),
                                      generator.choice(["High", "Medium", "Low"]), deadline)
            minutes = generator.randint(10, 300)
            plan = self.planner.generate_plan(minutes, today=TODAY)
            pool = [(t["importance_value"], t["estimated_duration"])
                    for t in plan["selected"] + plan["not_selected"]]
            best = 0
            for size in range(len(pool) + 1):
                for combo in itertools.combinations(pool, size):
                    if sum(w for _, w in combo) <= minutes:
                        best = max(best, sum(v for v, _ in combo))
            self.assertEqual(plan["total_value"], best)

    def test_insufficient_time(self):
        self.add_sample_topics()
        plan = self.planner.generate_plan(20, today=TODAY)
        self.assertEqual(plan["selected"], [])
        self.assertEqual(len(plan["not_selected"]), 7)
        self.assertEqual(plan["remaining"], 20)
        self.assertTrue(any("No topic fits" in w for w in plan["warnings"]))
        self.assertIn("more than all available time", plan["not_selected"][0]["reason"])

    def test_no_pending_topics(self):
        plan = self.planner.generate_plan(60, today=TODAY)
        self.assertEqual(plan["selected"], [])
        self.assertEqual(plan["remaining"], 60)
        self.assertTrue(plan["warnings"])
        self.assertIsNone(plan["knapsack"])

    def test_no_start_time_means_no_clock_times(self):
        self.add_sample_topics()
        plan = self.planner.generate_plan(120, today=TODAY)
        for topic in plan["selected"]:
            self.assertIsNone(topic["start_time"])
            self.assertIsNone(topic["end_time"])

    def test_start_time_gives_back_to_back_sessions(self):
        self.add_sample_topics()
        plan = self.planner.generate_plan(120, start_time="09:00", today=TODAY)
        slots = [(t["start_time"], t["end_time"]) for t in plan["selected"]]
        self.assertEqual(slots, [("09:00", "09:35"), ("09:35", "10:05"), ("10:05", "10:55")])

    def test_busy_slots_are_skipped(self):
        self.add_sample_topics()
        busy = [{"start_time": "09:30", "end_time": "10:30"}]
        plan = self.planner.generate_plan(120, start_time="09:00", busy_slots=busy, today=TODAY)
        # the first topic needs 35 min, so 09:00-09:35 would hit the busy slot: it jumps to 10:30
        self.assertEqual(plan["selected"][0]["start_time"], "10:30")
        for topic in plan["selected"]:
            start = int(topic["start_time"][:2]) * 60 + int(topic["start_time"][3:])
            end = int(topic["end_time"][:2]) * 60 + int(topic["end_time"][3:])
            self.assertTrue(end <= 9 * 60 + 30 or start >= 10 * 60 + 30)

    def test_sessions_never_overlap(self):
        self.add_sample_topics()
        busy = [{"start_time": "10:00", "end_time": "10:30"},
                {"start_time": "11:00", "end_time": "11:15"}]
        for algorithm in ["Merge Sort", "Insertion Sort", "Quick Sort", "Heap Sort"]:
            for sort_by in ["Deadline", "Priority", "Duration", "Name"]:
                with self.subTest(algorithm=algorithm, sort_by=sort_by):
                    plan = self.planner.generate_plan(300, sort_by=sort_by, algorithm=algorithm,
                                                      start_time="09:00", busy_slots=busy, today=TODAY)
                    self.assertEqual(self.schedule.find_overlaps(plan["selected"]), [])
                    self.assertEqual(self.schedule.find_overlaps(plan["selected"] + [
                        {"topic_name": "busy1", "start_time": "10:00", "end_time": "10:30"},
                        {"topic_name": "busy2", "start_time": "11:00", "end_time": "11:15"}]), [])

    def test_topic_that_does_not_fit_before_midnight_gets_warning(self):
        sid = self.subjects.add_subject("S")
        self.topics.add_topic(sid, "Long", 60, "High")
        plan = self.planner.generate_plan(120, start_time="23:30", today=TODAY)
        self.assertEqual(len(plan["selected"]), 1)  # still selected ...
        self.assertIsNone(plan["selected"][0]["start_time"])  # ... but no clock time
        self.assertTrue(any("midnight" in w for w in plan["warnings"]))

    def test_urgency_bonus_table(self):
        expected = {None: 0, -5: 3, 0: 3, 1: 2, 3: 2, 4: 1, 7: 1, 8: 0, 100: 0}
        for days, bonus in expected.items():
            with self.subTest(days=days):
                self.assertEqual(self.planner.urgency_bonus(days), bonus)

    def test_importance_values(self):
        self.add_sample_topics()
        plan = self.planner.generate_plan(1440, today=TODAY)
        values = {t["topic_name"]: t["importance_value"]
                  for t in plan["selected"] + plan["not_selected"]}
        # priority points + deadline bonus
        self.assertEqual(values, {"Arrays": 7, "Trees": 6, "Graphs": 3, "Sorting": 1,
                                  "SQL": 6, "Joins": 7, "Normalization": 4})

    def test_deadlines_can_be_switched_off(self):
        self.add_sample_topics()
        plan = self.planner.generate_plan(1440, today=TODAY, use_deadline_urgency=False)
        values = {t["topic_name"]: t["importance_value"] for t in plan["selected"]}
        self.assertEqual(values["Arrays"], 5)
        self.assertEqual(values["Normalization"], 1)
        self.assertTrue(all(t["urgency_bonus"] == 0 for t in plan["selected"]))

    def test_plan_for_one_subject(self):
        self.add_sample_topics()
        plan = self.planner.generate_plan(1440, subject_id=self.dbms, today=TODAY)
        self.assertEqual(sorted(self.names(plan["selected"])), ["Joins", "Normalization", "SQL"])

    def test_regenerating_reflects_changes(self):
        self.add_sample_topics()
        first = self.planner.generate_plan(60, today=TODAY)
        self.topics.add_topic(self.dsa, "Urgent", 55, "High", "2026-12-01")
        second = self.planner.generate_plan(60, today=TODAY)
        self.assertNotIn("Urgent", self.names(first["selected"]))
        self.assertIn("Urgent", self.names(second["selected"]))
        third = self.planner.generate_plan(200, today=TODAY)
        self.assertGreater(third["total_value"], second["total_value"])

    def test_explanation_names_the_algorithms(self):
        self.add_sample_topics()
        plan = self.planner.generate_plan(120, algorithm="Quick Sort", start_time="09:00", today=TODAY)
        text = " ".join(plan["explanation"])
        self.assertIn("Quick Sort", text)
        self.assertIn("0/1 Knapsack", text)
        self.assertIn("Activity Selection", text)

    def test_every_sort_algorithm_gives_a_valid_plan(self):
        self.add_sample_topics()
        for algorithm in ["Merge Sort", "Insertion Sort", "Quick Sort", "Heap Sort"]:
            with self.subTest(algorithm=algorithm):
                plan = self.planner.generate_plan(120, algorithm=algorithm, today=TODAY)
                self.assertEqual(plan["total_value"], 18)


# ======================================================================
# Schedule manager
# ======================================================================
class TestScheduleManager(BaseTest):
    DAY = "2026-12-01"

    def make_plan(self, minutes=120, start_time="09:00", busy=None):
        if not self.topics.list_topics():
            self.add_sample_topics()
        return self.planner.generate_plan(minutes, start_time=start_time, busy_slots=busy, today=TODAY)

    def test_save_and_view_timed_plan(self):
        plan = self.make_plan()
        self.assertEqual(self.schedule.save_plan(plan, self.DAY), 3)
        sessions = self.schedule.get_daily_sessions(self.DAY)
        self.assertEqual([s["topic_name"] for s in sessions], ["Normalization", "Arrays", "Joins"])
        self.assertEqual(sessions[0]["time_label"], "09:00-09:35")
        self.assertEqual(sessions[0]["allocated_duration"], 35)
        self.assertEqual(sessions[0]["subject_name"], "DBMS")
        self.assertTrue(all(s["status"] == "Pending" for s in sessions))

    def test_plan_without_times_shows_no_invented_clock_times(self):
        plan = self.make_plan(start_time="")
        self.schedule.save_plan(plan, self.DAY)
        for session in self.schedule.get_daily_sessions(self.DAY):
            self.assertIsNone(session["start_time"])
            self.assertEqual(session["time_label"], "No clock time")

    def test_saving_again_replaces_pending_sessions(self):
        plan = self.make_plan()
        self.schedule.save_plan(plan, self.DAY)
        self.schedule.save_plan(plan, self.DAY)
        self.assertEqual(len(self.schedule.get_daily_sessions(self.DAY)), 3)  # no duplicates

    def test_other_dates_are_not_touched(self):
        plan = self.make_plan()
        self.schedule.save_plan(plan, "2026-12-02")
        self.schedule.save_plan(plan, self.DAY)
        self.assertEqual(len(self.schedule.get_daily_sessions("2026-12-02")), 3)
        self.assertEqual(self.schedule.list_session_dates(), ["2026-12-01", "2026-12-02"])

    def test_completed_sessions_survive_a_new_plan(self):
        self.schedule.save_plan(self.make_plan(), self.DAY)
        first = self.schedule.get_daily_sessions(self.DAY)[0]
        self.schedule.complete_session(first["session_id"])
        busy = self.schedule.busy_slots_for_date(self.DAY)
        self.assertEqual([(b["start_time"], b["end_time"]) for b in busy], [("09:00", "09:35")])
        new_plan = self.planner.generate_plan(120, start_time="09:00", busy_slots=busy, today=TODAY)
        self.schedule.save_plan(new_plan, self.DAY)
        sessions = self.schedule.get_daily_sessions(self.DAY)
        self.assertEqual(sessions[0]["session_id"], first["session_id"])
        self.assertEqual(sessions[0]["status"], "Completed")
        self.assertEqual(self.schedule.find_overlaps(sessions), [])

    def test_overlap_with_kept_session_is_refused_and_nothing_changes(self):
        self.schedule.save_plan(self.make_plan(), self.DAY)
        first = self.schedule.get_daily_sessions(self.DAY)[0]
        self.schedule.complete_session(first["session_id"])
        before = [s["session_id"] for s in self.schedule.get_daily_sessions(self.DAY)]
        clashing = self.planner.generate_plan(120, start_time="09:15", today=TODAY)
        with self.assertRaises(DatabaseError):
            self.schedule.save_plan(clashing, self.DAY)
        after = [s["session_id"] for s in self.schedule.get_daily_sessions(self.DAY)]
        self.assertEqual(before, after)

    def test_save_rejects_bad_input(self):
        plan = self.make_plan()
        with self.assertRaises(DatabaseError):
            self.schedule.save_plan(plan, "")
        with self.assertRaises(DatabaseError):
            self.schedule.save_plan(plan, "01-12-2026")
        with self.assertRaises(DatabaseError):
            self.schedule.save_plan({"selected": []}, self.DAY)
        with self.assertRaises(DatabaseError):
            self.schedule.save_plan(None, self.DAY)

    def test_complete_and_reopen_session(self):
        self.schedule.save_plan(self.make_plan(), self.DAY)
        session = self.schedule.get_daily_sessions(self.DAY)[0]
        self.schedule.complete_session(session["session_id"])
        self.assertEqual(self.topics.get_topic(session["topic_id"])["status"], "Completed")
        self.assertEqual(len(self.schedule.get_pending_sessions()), 2)
        self.schedule.reopen_session(session["session_id"])
        self.assertEqual(self.topics.get_topic(session["topic_id"])["status"], "Pending")
        self.assertEqual(len(self.schedule.get_pending_sessions()), 3)

    def test_complete_session_without_completing_topic(self):
        self.schedule.save_plan(self.make_plan(), self.DAY)
        session = self.schedule.get_daily_sessions(self.DAY)[0]
        self.schedule.complete_session(session["session_id"], complete_topic=False)
        self.assertEqual(self.topics.get_topic(session["topic_id"])["status"], "Pending")

    def test_day_summary(self):
        self.schedule.save_plan(self.make_plan(), self.DAY)
        first = self.schedule.get_daily_sessions(self.DAY)[0]
        self.schedule.complete_session(first["session_id"])
        summary = self.schedule.day_summary(self.DAY)
        self.assertEqual(summary, {"sessions": 3, "completed": 1, "pending": 2,
                                   "total_minutes": 115, "completed_minutes": 35})
        empty = self.schedule.day_summary("2030-01-01")
        self.assertEqual(empty["sessions"], 0)

    def test_empty_schedule(self):
        self.assertEqual(self.schedule.get_schedule(), [])
        self.assertEqual(self.schedule.get_pending_sessions(), [])
        self.assertEqual(self.schedule.list_session_dates(), [])

    def test_missing_session_and_bad_date(self):
        for action in [lambda: self.schedule.complete_session(999),
                       lambda: self.schedule.reopen_session(999),
                       lambda: self.schedule.delete_session(999),
                       lambda: self.schedule.get_daily_sessions("not a date")]:
            with self.assertRaises(DatabaseError):
                action()

    def test_delete_session(self):
        self.schedule.save_plan(self.make_plan(), self.DAY)
        session = self.schedule.get_daily_sessions(self.DAY)[0]
        self.schedule.delete_session(session["session_id"])
        self.assertEqual(len(self.schedule.get_daily_sessions(self.DAY)), 2)

    def test_find_overlaps(self):
        def slot(name, start, end):
            return {"topic_name": name, "start_time": start, "end_time": end}

        self.assertEqual(self.schedule.find_overlaps([]), [])
        self.assertEqual(self.schedule.find_overlaps([slot("A", "09:00", "10:00")]), [])
        # touching is allowed
        self.assertEqual(self.schedule.find_overlaps(
            [slot("A", "09:00", "10:00"), slot("B", "10:00", "11:00")]), [])
        # real overlap, given out of order
        pairs = self.schedule.find_overlaps([slot("B", "09:30", "10:30"), slot("A", "09:00", "10:00")])
        self.assertEqual([(a["topic_name"], b["topic_name"]) for a, b in pairs], [("A", "B")])
        # a long session that contains a short one
        pairs = self.schedule.find_overlaps([slot("Long", "09:00", "12:00"), slot("Short", "10:00", "10:30"),
                                             slot("Later", "11:00", "11:30")])
        self.assertEqual(len(pairs), 2)
        # sessions without clock times are ignored
        self.assertEqual(self.schedule.find_overlaps(
            [slot("A", None, None), slot("B", None, None)]), [])

    def test_find_overlaps_matches_brute_force(self):
        generator = random.Random(12)
        for _ in range(300):
            sessions = []
            for i in range(generator.randint(0, 7)):
                start = generator.randint(0, 600)
                end = start + generator.randint(1, 120)
                sessions.append({"topic_name": str(i),
                                 "start_time": "%02d:%02d" % (start // 60, start % 60),
                                 "end_time": "%02d:%02d" % (end // 60, end % 60),
                                 "s": start, "e": end})
            expected = any(a["s"] < b["e"] and b["s"] < a["e"]
                           for i, a in enumerate(sessions) for b in sessions[i + 1:])
            self.assertEqual(bool(self.schedule.find_overlaps(sessions)), expected)


# ======================================================================
# Progress tracker
# ======================================================================
class TestProgressTracker(BaseTest):
    def test_helpers(self):
        self.assertEqual(percent(1, 3), 33.3)
        self.assertEqual(percent(0, 0), 0.0)
        self.assertEqual(percent(5, 5), 100.0)
        self.assertEqual([format_minutes(m) for m in (0, 45, 60, 90, 135)],
                         ["0m", "45m", "1h", "1h 30m", "2h 15m"])

    def test_empty_database_does_not_crash(self):
        overall = self.progress.overall_progress()
        self.assertEqual(overall["total_topics"], 0)
        self.assertEqual(overall["completion_percent"], 0.0)
        self.assertEqual(overall["studied_minutes"], 0)
        self.assertEqual(self.progress.subject_progress(), [])
        stats = self.progress.dashboard_stats(TODAY)
        self.assertEqual(stats["total_subjects"], 0)
        self.assertEqual(stats["overall_percent"], 0.0)
        self.assertEqual(stats["upcoming_deadlines"], [])
        self.assertEqual(stats["todays_sessions"], [])

    def test_overall_numbers_come_from_the_database(self):
        self.add_sample_topics()
        overall = self.progress.overall_progress()
        self.assertEqual(overall["total_topics"], 7)
        self.assertEqual(overall["pending_topics"], 7)
        self.assertEqual(overall["total_minutes"], 310)
        self.assertEqual(overall["completion_percent"], 0.0)

        arrays = self.topics.list_topics(keyword="Arrays")[0]
        self.topics.mark_completed(arrays["topic_id"])
        overall = self.progress.overall_progress()
        self.assertEqual(overall["completed_topics"], 1)
        self.assertEqual(overall["completion_percent"], 14.3)
        self.assertEqual(overall["completed_minutes"], 30)
        self.assertEqual(overall["pending_minutes"], 280)

        self.topics.delete_topic(arrays["topic_id"])  # deleting changes the numbers too
        overall = self.progress.overall_progress()
        self.assertEqual(overall["total_topics"], 6)
        self.assertEqual(overall["completed_topics"], 0)

    def test_subject_progress(self):
        self.add_sample_topics()
        self.subjects.add_subject("Operating Systems")  # no topics
        self.topics.mark_completed(self.topics.list_topics(keyword="Arrays")[0]["topic_id"])
        rows = {r["subject_name"]: r for r in self.progress.subject_progress()}
        self.assertEqual(rows["Data Structures"]["completed_topics"], 1)
        self.assertEqual(rows["Data Structures"]["total_topics"], 4)
        self.assertEqual(rows["Data Structures"]["percent"], 25.0)
        self.assertEqual(rows["DBMS"]["percent"], 0.0)
        self.assertEqual(rows["Operating Systems"]["total_topics"], 0)
        self.assertEqual(rows["Operating Systems"]["percent"], 0.0)

    def test_session_numbers(self):
        self.add_sample_topics()
        self.schedule.save_plan(self.planner.generate_plan(120, start_time="09:00", today=TODAY),
                                "2026-12-01")
        first = self.schedule.get_daily_sessions("2026-12-01")[0]
        self.schedule.complete_session(first["session_id"])
        overall = self.progress.overall_progress()
        self.assertEqual(overall["total_sessions"], 3)
        self.assertEqual(overall["completed_sessions"], 1)
        self.assertEqual(overall["pending_sessions"], 2)
        self.assertEqual(overall["studied_minutes"], first["allocated_duration"])

    def test_upcoming_deadlines(self):
        self.add_sample_topics()
        self.topics.add_topic(self.dsa, "Indexes", 20, "Low")  # no deadline: never listed
        done = self.topics.list_topics(keyword="Joins")[0]
        self.topics.mark_completed(done["topic_id"])  # completed: never listed
        rows = self.progress.upcoming_deadlines(limit=10, today=TODAY)
        self.assertEqual(self.names(rows), ["Normalization", "SQL", "Arrays", "Trees", "Graphs"])
        self.assertTrue(rows[0]["overdue"])
        self.assertEqual(rows[0]["days_left"], -3)
        self.assertFalse(rows[1]["overdue"])
        self.assertEqual(rows[1]["days_left"], 0)
        self.assertEqual(len(self.progress.upcoming_deadlines(limit=2, today=TODAY)), 2)

    def test_dashboard_stats(self):
        self.add_sample_topics()
        self.schedule.save_plan(self.planner.generate_plan(120, start_time="09:00", today=TODAY),
                                "2026-12-01")
        stats = self.progress.dashboard_stats(TODAY)
        self.assertEqual(stats["total_subjects"], 2)
        self.assertEqual(stats["total_topics"], 7)
        self.assertEqual(stats["pending_topics"], 7)
        self.assertEqual(stats["total_estimated_hours"], 5.2)
        self.assertEqual(len(stats["todays_sessions"]), 3)
        self.assertEqual(len(stats["upcoming_deadlines"]), 5)
        other_day = self.progress.dashboard_stats(date(2026, 12, 9))
        self.assertEqual(other_day["todays_sessions"], [])


# ======================================================================
# Whole workflow
# ======================================================================
class TestWholeWorkflow(BaseTest):
    def test_subject_to_progress(self):
        sid = self.subjects.add_subject("Algorithms", "CSE221")
        self.topics.add_topic(sid, "Sorting", 40, "High", "2026-12-02")
        self.topics.add_topic(sid, "Greedy", 30, "Medium", "2026-12-04")
        self.topics.add_topic(sid, "Dynamic Programming", 60, "High", "2026-12-03")

        plan = self.planner.generate_plan(100, start_time="08:00", today=TODAY)
        self.assertEqual(plan["total_allocated"], 100)
        self.assertEqual(self.names(plan["selected"]), ["Sorting", "Dynamic Programming"])

        self.schedule.save_plan(plan, "2026-12-01")
        for session in self.schedule.get_daily_sessions("2026-12-01"):
            self.schedule.complete_session(session["session_id"])

        stats = self.progress.dashboard_stats(TODAY)
        self.assertEqual(stats["completed_topics"], 2)
        self.assertEqual(stats["pending_topics"], 1)
        self.assertEqual(stats["overall_percent"], 66.7)

        # the next plan only contains what is still pending
        next_plan = self.planner.generate_plan(100, today=TODAY)
        self.assertEqual(self.names(next_plan["selected"]), ["Greedy"])

    def test_data_survives_a_restart(self):
        self.add_sample_topics()
        self.schedule.save_plan(self.planner.generate_plan(120, today=TODAY), "2026-12-01")
        # new manager objects = like closing and re-opening the application
        self.assertEqual(len(SubjectManager().list_subjects()), 2)
        self.assertEqual(len(TopicManager().list_topics()), 7)
        self.assertEqual(len(ScheduleManager().get_schedule()), 3)
        self.assertEqual(ProgressTracker().overall_progress()["total_topics"], 7)


if __name__ == "__main__":
    unittest.main()