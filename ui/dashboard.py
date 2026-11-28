"""
dashboard.py - the Dashboard, the home screen (Phase 5).

Shows the main numbers at a glance: subjects, topics, completed and pending
topics, estimated study time, overall progress, the nearest deadlines and
today's study sessions. Everything is read from the database by
ProgressTracker every time the page is opened, so it is always up to date
after you add, edit, delete or complete something on another page.
"""

from datetime import date
from tkinter import ttk

from modules.progress_tracker import ProgressTracker
from ui import styles


def due_text(days_left, overdue):
    """'3 days late', 'today', 'tomorrow' or 'in 5 days'."""
    if days_left is None:
        return "-"
    if overdue:
        late = abs(days_left)
        return str(late) + (" day late" if late == 1 else " days late")
    if days_left == 0:
        return "today"
    if days_left == 1:
        return "tomorrow"
    return "in " + str(days_left) + " days"


class DashboardPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.tracker = ProgressTracker()

        self._build_header()
        self._build_cards()
        self._build_progress()
        self._build_tables()

    # ------------------------------------------------------------------
    # Building the page
    # ------------------------------------------------------------------
    def _build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x")
        titles = ttk.Frame(header)
        titles.pack(side="left")
        ttk.Label(titles, text="Dashboard", style="Title.TLabel").pack(anchor="w")
        self.date_label = ttk.Label(titles, text="", style="Subtitle.TLabel")
        self.date_label.pack(anchor="w", pady=(2, 0))

        # Quick actions
        ttk.Button(header, text="Generate Study Plan", style="Primary.TButton",
                   command=lambda: self.app.show_page("Generate Study Plan")).pack(side="right")
        ttk.Button(header, text="Add Topic",
                   command=lambda: self.app.show_page("Study Topics")).pack(side="right", padx=(0, 8))

    def _build_cards(self):
        cards = ttk.Frame(self)
        cards.pack(fill="x", pady=(16, 12))
        self.subjects_card = styles.StatCard(cards, "Total subjects", styles.PRIMARY)
        self.topics_card = styles.StatCard(cards, "Study topics", styles.PURPLE)
        self.completed_card = styles.StatCard(cards, "Completed", styles.SUCCESS)
        self.pending_card = styles.StatCard(cards, "Pending", styles.WARNING)
        self.hours_card = styles.StatCard(cards, "Estimated study time", styles.TEAL)
        for column, card in enumerate([self.subjects_card, self.topics_card, self.completed_card,
                                       self.pending_card, self.hours_card]):
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 10, 0))
            cards.columnconfigure(column, weight=1)

    def _build_progress(self):
        card = styles.Card(self)
        card.pack(fill="x", pady=(0, 12))
        inner = ttk.Frame(card, style="Card.TFrame", padding=(16, 12))
        inner.pack(fill="x")
        self.progress_row = styles.ProgressRow(inner, "Overall study progress", label_width=22)
        self.progress_row.pack(fill="x")

    def _build_tables(self):
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1, uniform="half")
        body.columnconfigure(1, weight=1, uniform="half")

        # Left: upcoming deadlines
        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(left, text="Upcoming deadlines", style="Heading.TLabel").pack(anchor="w")
        self.deadline_note = ttk.Label(left, text="", style="Muted.TLabel")
        self.deadline_note.pack(anchor="w", pady=(0, 6))
        columns = [("topic", "Topic", 105, "w"), ("subject", "Subject", 115, "w"),
                   ("deadline", "Deadline", 85, "center"), ("due", "Due", 90, "center")]
        container, self.deadline_tree = styles.make_table(left, columns, height=6)
        container.pack(fill="both", expand=True)

        # Right: today's sessions
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ttk.Label(right, text="Today's study sessions", style="Heading.TLabel").pack(anchor="w")
        self.session_note = ttk.Label(right, text="", style="Muted.TLabel")
        self.session_note.pack(anchor="w", pady=(0, 6))
        columns = [("time", "Time", 92, "center"), ("topic", "Topic", 90, "w"),
                   ("subject", "Subject", 105, "w"), ("minutes", "Min", 40, "e"),
                   ("status", "Status", 85, "center")]
        container, self.session_tree = styles.make_table(right, columns, height=6)
        container.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Showing data
    # ------------------------------------------------------------------
    def refresh(self):
        """Called by the main window every time this page is opened."""
        today = date.today()
        stats = self.tracker.dashboard_stats(today)
        self.date_label.config(text=today.strftime("%A, %d %B %Y") + "  -  your study overview")

        self.subjects_card.set(stats["total_subjects"], "courses")
        self.topics_card.set(stats["total_topics"], "in total")
        self.completed_card.set(stats["completed_topics"], "topics done")
        self.pending_card.set(stats["pending_topics"], "still to study")
        self.hours_card.set(str(stats["total_estimated_hours"]) + " h", "for all topics")

        self.progress_row.set(stats["overall_percent"],
                              str(stats["completed_topics"]) + " of " + str(stats["total_topics"])
                              + " topics (" + str(stats["overall_percent"]) + "%)")

        self._fill_deadlines(stats["upcoming_deadlines"])
        self._fill_sessions(stats["todays_sessions"])

    def _fill_deadlines(self, deadlines):
        rows = []
        tags = []
        overdue = 0
        for topic in deadlines:
            if topic["overdue"]:
                overdue += 1
            rows.append((topic["topic_name"], topic["subject_name"], topic["deadline"],
                         due_text(topic["days_left"], topic["overdue"])))
            tags.append("Overdue" if topic["overdue"] else topic["priority"])
        styles.fill_table(self.deadline_tree, rows, tags=tags)

        if not deadlines:
            self.deadline_note.config(text="No pending topic has a deadline.")
        elif overdue:
            self.deadline_note.config(text=str(overdue) + " overdue - shown in red")
        else:
            self.deadline_note.config(text="Nearest deadlines of your pending topics")

    def _fill_sessions(self, sessions):
        rows = []
        tags = []
        done = 0
        for session in sessions:
            rows.append((session["time_label"], session["topic_name"], session["subject_name"],
                         session["allocated_duration"], session["status"]))
            tags.append(styles.row_tag(session["priority"], session["status"]))
            if session["is_completed"]:
                done += 1
        styles.fill_table(self.session_tree, rows, tags=tags)

        if sessions:
            self.session_note.config(text=str(done) + " of " + str(len(sessions))
                                     + " session(s) completed today")
        else:
            self.session_note.config(text="Nothing planned for today. Generate a plan and "
                                     "save it to today's date.")