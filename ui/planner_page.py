"""
planner_page.py - the Generate Study Plan page (Phase 5).

The student enters the available study time and this page shows the plan made
by StudyPlanner (sorting + 0/1 Knapsack + Activity Selection). The plan can then
be saved as study sessions for a date. This page never writes SQL.
"""

import tkinter as tk
from datetime import date
from tkinter import ttk

from database import DatabaseError
from modules.progress_tracker import format_minutes
from modules.schedule_manager import ScheduleManager
from modules.study_planner import StudyPlanner
from modules.subject_manager import SubjectManager
from modules.topic_manager import SORT_ALGORITHMS, SORT_CRITERIA
from ui import styles

ALL_SUBJECTS = "All subjects"

WHY_THESE_ALGORITHMS = [
    "0/1 Knapsack (dynamic programming) chooses the topics. A topic cannot be studied "
    "half-way, so it takes whole topics only and finds the combination with the largest "
    "total importance that fits in your time.",
    "Sorting (the algorithm and column you picked) puts the chosen topics in study order.",
    "Activity Selection checks the clock times when you give a start time: it confirms "
    "that no two sessions overlap.",
]


class PlannerPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Style(self).configure("Card.TCheckbutton", background=styles.CARD_BG)  # white, like the card
        self.planner = StudyPlanner()
        self.schedule = ScheduleManager()
        self.subjects = SubjectManager()
        self.plan = None          # the plan on screen (None = nothing generated yet)
        self.subject_ids = {}     # subject name -> subject id

        styles.PageHeader(self, "Generate Study Plan",
                          "Tell me how much time you have and I will choose the best topics"
                          ).pack(anchor="w")
        self._build_inputs()
        self._build_results()
        self._show_plan(None)

    # ------------------------------------------------------------------
    # Building the page
    # ------------------------------------------------------------------
    def _build_inputs(self):
        card = styles.Card(self)
        card.pack(fill="x", pady=(14, 10))
        form = ttk.Frame(card, style="Card.TFrame", padding=14)
        form.pack(fill="x")

        self.time_var = tk.StringVar(value="120")
        self.unit_var = tk.StringVar(value="minutes")
        self.subject_var = tk.StringVar(value=ALL_SUBJECTS)
        self.start_var = tk.StringVar()
        self.sort_var = tk.StringVar(value="Deadline")
        self.algorithm_var = tk.StringVar(value="Merge Sort")
        self.urgency_var = tk.BooleanVar(value=True)
        self.date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))

        labels = [("Available study time *", 0, 2), ("Subject", 2, 1),
                  ("Start time (HH:MM, optional)", 3, 1), ("Sort topics by", 4, 1), ("using", 5, 1)]
        for text, column, span in labels:
            ttk.Label(form, text=text, style="Card.TLabel").grid(
                row=0, column=column, columnspan=span, sticky="w",
                padx=(0 if column == 0 else 10, 0))

        self.time_entry = ttk.Entry(form, textvariable=self.time_var, width=7)
        self.time_entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        ttk.Combobox(form, textvariable=self.unit_var, state="readonly", width=8,
                     values=["minutes", "hours"]).grid(row=1, column=1, sticky="ew",
                                                       padx=(6, 0), pady=(4, 0))
        self.subject_combo = ttk.Combobox(form, textvariable=self.subject_var,
                                          state="readonly", width=18)
        self.subject_combo.grid(row=1, column=2, sticky="ew", padx=(10, 0), pady=(4, 0))
        self.start_entry = ttk.Entry(form, textvariable=self.start_var, width=8)
        self.start_entry.grid(row=1, column=3, sticky="ew", padx=(10, 0), pady=(4, 0))
        ttk.Combobox(form, textvariable=self.sort_var, state="readonly", width=10,
                     values=list(SORT_CRITERIA)).grid(row=1, column=4, sticky="ew",
                                                      padx=(10, 0), pady=(4, 0))
        ttk.Combobox(form, textvariable=self.algorithm_var, state="readonly", width=14,
                     values=list(SORT_ALGORITHMS)).grid(row=1, column=5, sticky="ew",
                                                        padx=(10, 0), pady=(4, 0))
        form.columnconfigure(2, weight=1)

        ttk.Checkbutton(form, text="Add deadline urgency to each topic's importance",
                        variable=self.urgency_var, style="Card.TCheckbutton"
                        ).grid(row=2, column=0, columnspan=6, sticky="w", pady=(10, 0))

        buttons = ttk.Frame(form, style="Card.TFrame")
        buttons.grid(row=3, column=0, columnspan=6, sticky="ew", pady=(10, 0))
        ttk.Button(buttons, text="Generate Plan", style="Primary.TButton",
                   command=self.generate_plan).pack(side="left")
        self.save_button = ttk.Button(buttons, text="Save to Schedule", style="Success.TButton",
                                      command=self.save_plan)
        self.save_button.pack(side="right")
        ttk.Entry(buttons, textvariable=self.date_var, width=12).pack(side="right", padx=(6, 10))
        ttk.Label(buttons, text="Save on date:", style="Card.TLabel").pack(side="right")

        for entry in (self.time_entry, self.start_entry):
            entry.bind("<Return>", lambda e: self.generate_plan())

    def _build_results(self):
        cards = ttk.Frame(self)
        cards.pack(fill="x", pady=(0, 6))
        self.available_card = styles.StatCard(cards, "Available time", styles.PRIMARY)
        self.allocated_card = styles.StatCard(cards, "Allocated time", styles.SUCCESS)
        self.remaining_card = styles.StatCard(cards, "Remaining time", styles.WARNING)
        self.value_card = styles.StatCard(cards, "Total importance", styles.PURPLE)
        for column, card in enumerate([self.available_card, self.allocated_card,
                                       self.remaining_card, self.value_card]):
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 10, 0))
            cards.columnconfigure(column, weight=1)

        self.status_label = tk.Label(self, text="", bg=styles.BG, fg=styles.MUTED,
                                     font=styles.FONT_BASE, anchor="w", justify="left")
        self.status_label.pack(fill="x", pady=(0, 6))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: the plan
        plan_tab = ttk.Frame(self.notebook, padding=(0, 8, 0, 0))
        self.notebook.add(plan_tab, text="Study plan")
        columns = [("order", "Order", 55, "center"), ("topic", "Topic", 145, "w"),
                   ("subject", "Subject", 125, "w"), ("priority", "Priority", 70, "center"),
                   ("value", "Importance", 105, "center"), ("estimated", "Estimated", 90, "e"),
                   ("allocated", "Allocated", 90, "e"), ("deadline", "Deadline", 95, "center"),
                   ("start", "Start", 60, "center"), ("end", "End", 60, "center")]
        container, self.plan_tree = styles.make_table(plan_tab, columns, height=8)
        container.pack(fill="both", expand=True)

        # Tab 2: topics that were left out
        skipped_tab = ttk.Frame(self.notebook, padding=(0, 8, 0, 0))
        self.notebook.add(skipped_tab, text="Not selected")
        columns = [("topic", "Topic", 160, "w"), ("subject", "Subject", 130, "w"),
                   ("priority", "Priority", 75, "center"), ("minutes", "Minutes", 70, "e"),
                   ("value", "Importance", 105, "center"), ("reason", "Why it was not selected", 460, "w")]
        container, self.skipped_tree = styles.make_table(skipped_tab, columns, height=8)
        container.pack(fill="both", expand=True)

        # Tab 3: how the plan was made
        how_tab = ttk.Frame(self.notebook, padding=(0, 8, 0, 0))
        self.notebook.add(how_tab, text="How this plan was made")
        holder = styles.Card(how_tab)
        holder.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(holder, orient="vertical")
        self.how_text = tk.Text(holder, wrap="word", font=styles.FONT_BASE, bg="white",
                                relief="flat", padx=16, pady=12, height=8,
                                yscrollcommand=scrollbar.set, cursor="arrow")
        scrollbar.config(command=self.how_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.how_text.pack(side="left", fill="both", expand=True)
        self.how_text.tag_configure("heading", font=styles.FONT_BOLD, spacing3=6)
        self.how_text.tag_configure("step", spacing3=6)
        self.how_text.tag_configure("warning", foreground="#b45309", spacing3=6)
        self.how_text.tag_configure("muted", foreground=styles.MUTED, spacing3=6)

    # ------------------------------------------------------------------
    # Showing data
    # ------------------------------------------------------------------
    def refresh(self):
        """Called every time this page is opened: reload subjects and update the plan."""
        subjects = self.subjects.list_subjects()
        self.subject_ids = {s["subject_name"]: s["subject_id"] for s in subjects}
        self.subject_combo.config(values=[ALL_SUBJECTS] + list(self.subject_ids))
        if self.subject_var.get() not in self.subject_ids:
            self.subject_var.set(ALL_SUBJECTS)

        # Topics may have changed (added, completed, deleted): make the plan fresh again.
        if self.plan is not None:
            self.generate_plan(quiet=True)

    def _show_plan(self, plan):
        self.plan = plan
        self.plan_tree.delete(*self.plan_tree.get_children())
        self.skipped_tree.delete(*self.skipped_tree.get_children())
        self.how_text.config(state="normal")
        self.how_text.delete("1.0", "end")

        if plan is None:
            for card in (self.available_card, self.allocated_card,
                         self.remaining_card, self.value_card):
                card.set("-", "")
            self.status_label.config(text="Enter your available time and click Generate Plan.",
                                     fg=styles.MUTED)
            self.notebook.tab(1, text="Not selected")
            self.how_text.insert("end", "Generate a plan to see how it was made.", "muted")
            self.how_text.config(state="disabled")
            self.save_button.state(["disabled"])
            return

        selected = plan["selected"]
        self.available_card.set(format_minutes(plan["available_minutes"]),
                                str(plan["available_minutes"]) + " minutes")
        self.allocated_card.set(format_minutes(plan["total_allocated"]),
                                str(plan["total_allocated"]) + " min, "
                                + str(len(selected)) + " topic(s)")
        self.remaining_card.set(format_minutes(plan["remaining"]),
                                str(plan["remaining"]) + " minutes unused")
        self.value_card.set(plan["total_value"], "priority + deadline points")

        # The study plan table
        rows = []
        tags = []
        for topic in selected:
            value_text = str(topic["importance_value"])
            if topic["urgency_bonus"]:
                value_text += " (" + str(topic["priority_points"]) + "+" + str(topic["urgency_bonus"]) + ")"
            rows.append((topic["order"], topic["topic_name"], topic["subject_name"],
                         topic["priority"], value_text, topic["estimated_duration"],
                         topic["allocated_duration"], topic["deadline"] or "-",
                         topic["start_time"] or "-", topic["end_time"] or "-"))
            tags.append(topic["priority"])
        styles.fill_table(self.plan_tree, rows, tags=tags)

        # The "not selected" table
        rows = []
        tags = []
        for topic in plan["not_selected"]:
            rows.append((topic["topic_name"], topic["subject_name"], topic["priority"],
                         topic["estimated_duration"], topic["importance_value"],
                         topic["reason"]))
            tags.append(None)
        styles.fill_table(self.skipped_tree, rows, tags=tags)
        self.notebook.tab(1, text="Not selected (" + str(len(plan["not_selected"])) + ")")

        # Message line under the cards
        if plan["warnings"]:
            self.status_label.config(text=plan["warnings"][0], fg="#b45309")
        elif plan["not_selected"]:
            self.status_label.config(
                text=str(len(selected)) + " topic(s) chosen. " + str(len(plan["not_selected"]))
                + " topic(s) did not fit - see the 'Not selected' tab for the reasons.",
                fg=styles.MUTED)
        else:
            self.status_label.config(text="All pending topics fit into your time.", fg=styles.SUCCESS)

        # The explanation
        self.how_text.insert("end", "How this plan was made\n", "heading")
        for line in plan["explanation"]:
            self.how_text.insert("end", line + "\n", "step")
        self.how_text.insert("end", "\nWhy these algorithms?\n", "heading")
        for line in WHY_THESE_ALGORITHMS:
            self.how_text.insert("end", "\u2022 " + line + "\n", "step")
        for warning in plan["warnings"]:
            self.how_text.insert("end", "\nWarning: " + warning + "\n", "warning")
        self.how_text.config(state="disabled")

        if selected:
            self.save_button.state(["!disabled"])
        else:
            self.save_button.state(["disabled"])

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def generate_plan(self, quiet=False):
        """
        Make a plan from the values in the form. Clicking the button again with new
        values (or after topics changed) simply makes a fresh plan.
        quiet=True is used when the page refreshes by itself: problems do not pop up.
        """
        try:
            minutes = self.planner.parse_available_time(self.time_var.get(), self.unit_var.get())
            start_time = self.start_var.get().strip()

            busy = None
            if start_time:  # keep away from sessions already done on that date
                busy = self.schedule.busy_slots_for_date(self.date_var.get())

            plan = self.planner.generate_plan(
                minutes,
                sort_by=self.sort_var.get(),
                algorithm=self.algorithm_var.get(),
                start_time=start_time,
                busy_slots=busy,
                subject_id=self.subject_ids.get(self.subject_var.get()),
                use_deadline_urgency=self.urgency_var.get())
        except DatabaseError as error:
            if quiet:
                self._show_plan(None)
            else:
                styles.show_error(error)
            return
        self._show_plan(plan)

    def save_plan(self):
        if self.plan is None or not self.plan["selected"]:
            styles.show_warning("Generate a plan with at least one topic first.")
            return
        try:
            count = self.schedule.save_plan(self.plan, self.date_var.get())
        except DatabaseError as error:
            styles.show_error(error)
            return
        styles.show_info(str(count) + " session(s) saved for " + self.date_var.get().strip()
                         + ".\nOpen 'Study Schedule' in the sidebar to see them.\n\n"
                         "Saving again for the same date replaces the sessions that are "
                         "not completed yet.")