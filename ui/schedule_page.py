"""
schedule_page.py - the Study Schedule page (Phase 5).

Shows the study sessions that were saved from a plan: one day, all pending
sessions, or everything. A session can be marked completed (or pending again)
or deleted. This page only talks to ScheduleManager; it never writes SQL.
"""

import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import ttk

from database import DatabaseError
from modules.progress_tracker import format_minutes, percent
from modules.schedule_manager import ScheduleManager
from ui import styles

VIEW_DAILY = "Daily sessions"
VIEW_PENDING = "All pending sessions"
VIEW_ALL = "All sessions"


class SchedulePage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.schedule = ScheduleManager()

        self.view_var = tk.StringVar(value=VIEW_DAILY)
        self.date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.jump_var = tk.StringVar()

        styles.PageHeader(self, "Study Schedule",
                          "Your saved study sessions. Tick them off as you finish them"
                          ).pack(anchor="w")
        self._build_controls()
        self._build_summary()
        self._build_table()
        self._update_controls()

    # ------------------------------------------------------------------
    # Building the page
    # ------------------------------------------------------------------
    def _build_controls(self):
        card = styles.Card(self)
        card.pack(fill="x", pady=(14, 10))
        box = ttk.Frame(card, style="Card.TFrame", padding=(14, 12))
        box.pack(fill="x")

        row1 = ttk.Frame(box, style="Card.TFrame")
        row1.pack(fill="x")
        ttk.Label(row1, text="Show:", style="Card.TLabel").pack(side="left")
        view_combo = ttk.Combobox(row1, textvariable=self.view_var, state="readonly", width=22,
                                  values=[VIEW_DAILY, VIEW_PENDING, VIEW_ALL])
        view_combo.pack(side="left", padx=(8, 18))
        view_combo.bind("<<ComboboxSelected>>", lambda e: self._on_view_changed())

        ttk.Label(row1, text="Date:", style="Card.TLabel").pack(side="left")
        self.previous_button = ttk.Button(row1, text="<", width=3,
                                          command=lambda: self.shift_day(-1))
        self.previous_button.pack(side="left", padx=(8, 4))
        self.date_entry = ttk.Entry(row1, textvariable=self.date_var, width=12)
        self.date_entry.pack(side="left")
        self.date_entry.bind("<Return>", lambda e: self.show_day())
        self.next_button = ttk.Button(row1, text=">", width=3, command=lambda: self.shift_day(1))
        self.next_button.pack(side="left", padx=(4, 8))
        self.today_button = ttk.Button(row1, text="Today", command=self.go_today)
        self.today_button.pack(side="left", padx=(0, 6))
        self.show_button = ttk.Button(row1, text="Show", command=self.show_day)
        self.show_button.pack(side="left")

        row2 = ttk.Frame(box, style="Card.TFrame")
        row2.pack(fill="x", pady=(10, 0))
        ttk.Label(row2, text="Dates that have sessions:", style="Card.TLabel").pack(side="left")
        self.jump_combo = ttk.Combobox(row2, textvariable=self.jump_var, state="readonly", width=14)
        self.jump_combo.pack(side="left", padx=(8, 0))
        self.jump_combo.bind("<<ComboboxSelected>>", lambda e: self._on_jump())

    def _build_summary(self):
        card = styles.Card(self)
        card.pack(fill="x", pady=(0, 8))
        inner = ttk.Frame(card, style="Card.TFrame", padding=(14, 10))
        inner.pack(fill="x")
        self.progress_row = styles.ProgressRow(inner, "Completed", label_width=12)
        self.progress_row.pack(fill="x")

        self.message_label = tk.Label(self, text="", bg=styles.BG, fg=styles.MUTED,
                                      font=styles.FONT_BASE, anchor="w", justify="left")
        self.message_label.pack(fill="x", pady=(0, 6))

    def _build_table(self):
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(0, 8))
        self.toggle_button = ttk.Button(buttons, text="Mark Completed", style="Success.TButton",
                                        command=self.toggle_session)
        self.toggle_button.pack(side="left", padx=(0, 8))
        self.delete_button = ttk.Button(buttons, text="Delete Session", style="Danger.TButton",
                                        command=self.delete_session)
        self.delete_button.pack(side="left", padx=(0, 14))
        ttk.Label(buttons, text="Completing a session also marks its topic as completed.",
                  style="Muted.TLabel").pack(side="left")
        ttk.Button(buttons, text="Generate a new plan",
                   command=lambda: self.app.show_page("Generate Study Plan")).pack(side="right")

        columns = [("id", "ID", 45, "center"), ("date", "Date", 95, "center"),
                   ("time", "Time", 120, "center"), ("topic", "Topic", 170, "w"),
                   ("subject", "Subject", 150, "w"), ("priority", "Priority", 75, "center"),
                   ("minutes", "Allocated", 80, "e"), ("status", "Status", 90, "center")]
        container, self.tree = styles.make_table(self, columns, height=10)
        container.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._update_buttons())

    # ------------------------------------------------------------------
    # Showing data
    # ------------------------------------------------------------------
    def refresh(self):
        """Called by the main window every time this page is opened."""
        self.jump_combo.config(values=self.schedule.list_session_dates())
        self.refresh_table()

    def _is_daily(self):
        return self.view_var.get() == VIEW_DAILY

    def _update_controls(self):
        """The date controls only matter in the 'Daily sessions' view."""
        state = ["!disabled"] if self._is_daily() else ["disabled"]
        for widget in (self.previous_button, self.date_entry, self.next_button,
                       self.today_button, self.show_button):
            widget.state(state)

    def refresh_table(self, loud=False):
        """
        Reload the table. loud=True shows an error box for a bad date; otherwise
        the problem is only written in the message line.
        """
        previous = styles.selected_id(self.tree)  # keep the selection if the row is still there
        mode = self.view_var.get()
        sessions = []
        problem = ""
        try:
            if mode == VIEW_DAILY:
                if self.date_var.get().strip() == "":  # an empty date would list every day
                    raise DatabaseError("Please enter a date (YYYY-MM-DD).")
                sessions = self.schedule.get_daily_sessions(self.date_var.get())
            elif mode == VIEW_PENDING:
                sessions = self.schedule.get_pending_sessions()
            else:
                sessions = self.schedule.get_schedule()
        except DatabaseError as error:
            problem = str(error)
            if loud:
                styles.show_error(error)

        rows = []
        ids = []
        tags = []
        completed = 0
        total_minutes = 0
        for session in sessions:
            rows.append((session["session_id"], session["session_date"] or "-",
                         session["time_label"], session["topic_name"], session["subject_name"],
                         session["priority"], session["allocated_duration"], session["status"]))
            ids.append(session["session_id"])
            tags.append(styles.row_tag(session["priority"], session["status"]))
            total_minutes += session["allocated_duration"]
            if session["is_completed"]:
                completed += 1
        styles.fill_table(self.tree, rows, ids=ids, tags=tags)
        if previous is not None and self.tree.exists(str(previous)):
            self.tree.selection_set(str(previous))

        # Progress bar for what is listed
        if sessions:
            share = percent(completed, len(sessions))
            self.progress_row.set(share, str(completed) + " of " + str(len(sessions))
                                  + " sessions (" + str(share) + "%)")
        else:
            self.progress_row.set(0, "0 sessions")

        self._show_message(sessions, problem, total_minutes)
        self._update_buttons()

    def _show_message(self, sessions, problem, total_minutes):
        """One line under the progress bar: a problem, an overlap warning, or a summary."""
        if problem:
            self.message_label.config(text=problem, fg=styles.DANGER)
            return

        conflict = self._find_conflict(sessions)
        if conflict:
            self.message_label.config(text=conflict, fg="#b45309")
            return

        mode = self.view_var.get()
        if sessions:
            text = (str(len(sessions)) + " session(s), " + format_minutes(total_minutes)
                    + " planned")
            if mode == VIEW_DAILY:
                text += " on " + self.date_var.get().strip()
            self.message_label.config(text=text, fg=styles.MUTED)
        elif mode == VIEW_DAILY:
            self.message_label.config(
                text="No sessions on " + self.date_var.get().strip() + ". Generate a plan and "
                "save it to this date.", fg=styles.MUTED)
        elif mode == VIEW_PENDING:
            self.message_label.config(text="No pending sessions. Everything is done!",
                                      fg=styles.SUCCESS)
        else:
            self.message_label.config(text="No sessions saved yet. Generate a plan and "
                                      "click Save to Schedule.", fg=styles.MUTED)

    def _find_conflict(self, sessions):
        """Text about the first pair of overlapping sessions on one date, or ''."""
        by_date = {}
        for session in sessions:
            by_date.setdefault(session["session_date"], []).append(session)
        for day, day_sessions in by_date.items():
            overlaps = self.schedule.find_overlaps(day_sessions)
            if overlaps:
                first, second = overlaps[0]
                return ("Warning: sessions overlap on " + str(day) + ": '" + first["topic_name"]
                        + "' (" + first["time_label"] + ") and '" + second["topic_name"]
                        + "' (" + second["time_label"] + ").")
        return ""

    def _update_buttons(self):
        session_id = styles.selected_id(self.tree)
        if session_id is None:
            self.toggle_button.state(["disabled"])
            self.delete_button.state(["disabled"])
            self.toggle_button.config(text="Mark Completed")
            return
        status = self.tree.set(str(session_id), "status")
        self.toggle_button.config(text="Mark Pending" if status == "Completed" else "Mark Completed")
        self.toggle_button.state(["!disabled"])
        self.delete_button.state(["!disabled"])

    # ------------------------------------------------------------------
    # Date and view controls
    # ------------------------------------------------------------------
    def _on_view_changed(self):
        self._update_controls()
        self.refresh_table()

    def _on_jump(self):
        self.date_var.set(self.jump_var.get())
        self.view_var.set(VIEW_DAILY)
        self._update_controls()
        self.refresh_table()

    def show_day(self):
        self.refresh_table(loud=True)

    def go_today(self):
        self.date_var.set(date.today().strftime("%Y-%m-%d"))
        self.refresh_table()

    def shift_day(self, days):
        """Move the date forward or back. A date that cannot be read starts from today."""
        try:
            current = datetime.strptime(self.date_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            current = date.today()
        self.date_var.set((current + timedelta(days=days)).strftime("%Y-%m-%d"))
        self.refresh_table()

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def toggle_session(self):
        session_id = styles.selected_id(self.tree)
        if session_id is None:
            styles.show_warning("Click a session in the table first.")
            return
        try:
            if self.tree.set(str(session_id), "status") == "Completed":
                self.schedule.reopen_session(session_id)
            else:
                self.schedule.complete_session(session_id)
        except DatabaseError as error:
            styles.show_error(error)
        self.refresh_table()

    def delete_session(self):
        session_id = styles.selected_id(self.tree)
        if session_id is None:
            styles.show_warning("Click a session in the table first.")
            return
        topic = self.tree.set(str(session_id), "topic")
        if not styles.ask_yes_no("Delete this study session for '" + topic + "'?\n\n"
                                 "The topic itself is not deleted."):
            return
        try:
            self.schedule.delete_session(session_id)
        except DatabaseError as error:
            styles.show_error(error)
            return
        styles.show_info("Session deleted.")
        self.refresh()