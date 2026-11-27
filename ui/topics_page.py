"""
topics_page.py - the Study Topics page (Phase 5).

Add, edit, delete, search, filter, sort and complete study topics.
This page only talks to TopicManager and SubjectManager; it never writes SQL.
Every problem comes back as a DatabaseError, which is shown in an error box.
"""

import tkinter as tk
from tkinter import ttk

from database import DatabaseError, PRIORITIES
from modules.subject_manager import SubjectManager
from modules.topic_manager import TopicManager, SORT_ALGORITHMS, SORT_CRITERIA
from modules.progress_tracker import format_minutes
from ui import styles

ALL_SUBJECTS = "All subjects"
ALL_PRIORITIES = "All priorities"
ALL_STATUSES = "All statuses"
DEFAULT_ORDER = "Default order"


class TopicsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.topics = TopicManager()
        self.subjects = SubjectManager()
        self.selected_id = None   # id of the topic being edited (None = adding a new one)
        self.subject_ids = {}     # subject name -> subject id

        styles.PageHeader(self, "Study Topics",
                          "Add the topics you need to study, then filter, sort and tick them off"
                          ).pack(anchor="w")
        self._build_form()
        self._build_filters()
        self._build_table()
        self._set_editing(False)

    # ------------------------------------------------------------------
    # Building the page
    # ------------------------------------------------------------------
    def _build_form(self):
        card = styles.Card(self)
        card.pack(fill="x", pady=(14, 10))
        form = ttk.Frame(card, style="Card.TFrame", padding=14)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        self.subject_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.duration_var = tk.StringVar()
        self.priority_var = tk.StringVar(value="Medium")
        self.deadline_var = tk.StringVar()

        labels = ["Subject *", "Topic name *", "Minutes *", "Priority *", "Deadline (YYYY-MM-DD)"]
        for column, text in enumerate(labels):
            ttk.Label(form, text=text, style="Card.TLabel").grid(
                row=0, column=column, sticky="w", padx=(0 if column == 0 else 10, 0))

        self.subject_combo = ttk.Combobox(form, textvariable=self.subject_var, state="readonly", width=20)
        self.subject_combo.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.name_entry = ttk.Entry(form, textvariable=self.name_var)
        self.name_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(4, 0))
        self.duration_entry = ttk.Entry(form, textvariable=self.duration_var, width=8)
        self.duration_entry.grid(row=1, column=2, sticky="ew", padx=(10, 0), pady=(4, 0))
        self.priority_combo = ttk.Combobox(form, textvariable=self.priority_var, state="readonly",
                                           values=list(PRIORITIES), width=9)
        self.priority_combo.grid(row=1, column=3, sticky="ew", padx=(10, 0), pady=(4, 0))
        self.deadline_entry = ttk.Entry(form, textvariable=self.deadline_var, width=14)
        self.deadline_entry.grid(row=1, column=4, sticky="ew", padx=(10, 0), pady=(4, 0))

        for entry in (self.name_entry, self.duration_entry, self.deadline_entry):
            entry.bind("<Return>", lambda e: self.on_enter())
            entry.bind("<Escape>", lambda e: self.clear_form())

        buttons = ttk.Frame(form, style="Card.TFrame")
        buttons.grid(row=2, column=0, columnspan=5, sticky="w", pady=(12, 0))
        self.add_button = ttk.Button(buttons, text="Add Topic", style="Primary.TButton",
                                     command=self.add_topic)
        self.add_button.pack(side="left", padx=(0, 8))
        self.save_button = ttk.Button(buttons, text="Save Changes", style="Success.TButton",
                                      command=self.save_changes)
        self.save_button.pack(side="left", padx=(0, 8))
        self.toggle_button = ttk.Button(buttons, text="Mark Completed", command=self.toggle_status)
        self.toggle_button.pack(side="left", padx=(0, 8))
        self.delete_button = ttk.Button(buttons, text="Delete", style="Danger.TButton",
                                        command=self.delete_topic)
        self.delete_button.pack(side="left", padx=(0, 8))
        self.clear_button = ttk.Button(buttons, text="Clear", command=self.clear_form)
        self.clear_button.pack(side="left", padx=(0, 14))
        self.hint = ttk.Label(buttons, text="", style="CardMuted.TLabel")
        self.hint.pack(side="left")

    def _build_filters(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 8))

        self.search_var = tk.StringVar()
        self.filter_subject_var = tk.StringVar(value=ALL_SUBJECTS)
        self.filter_priority_var = tk.StringVar(value=ALL_PRIORITIES)
        self.filter_status_var = tk.StringVar(value=ALL_STATUSES)
        self.sort_var = tk.StringVar(value=DEFAULT_ORDER)
        self.algorithm_var = tk.StringVar(value="Merge Sort")

        # Row 1: search and filters
        row1 = ttk.Frame(bar)
        row1.pack(fill="x")
        ttk.Label(row1, text="Search:").pack(side="left")
        ttk.Entry(row1, textvariable=self.search_var, width=20).pack(side="left", padx=(6, 12))
        self.filter_subject_combo = ttk.Combobox(row1, textvariable=self.filter_subject_var,
                                                 state="readonly", width=22)
        self.filter_subject_combo.pack(side="left", padx=(0, 8))
        ttk.Combobox(row1, textvariable=self.filter_priority_var, state="readonly", width=13,
                     values=[ALL_PRIORITIES] + list(PRIORITIES)).pack(side="left", padx=(0, 8))
        ttk.Combobox(row1, textvariable=self.filter_status_var, state="readonly", width=13,
                     values=[ALL_STATUSES, "Pending", "Completed"]).pack(side="left", padx=(0, 8))
        ttk.Button(row1, text="Reset", command=self.reset_filters).pack(side="left")

        # Row 2: sorting (done with our own sorting algorithms)
        row2 = ttk.Frame(bar)
        row2.pack(fill="x", pady=(8, 0))
        ttk.Label(row2, text="Sort by:").pack(side="left")
        ttk.Combobox(row2, textvariable=self.sort_var, state="readonly", width=14,
                     values=[DEFAULT_ORDER] + list(SORT_CRITERIA)).pack(side="left", padx=(6, 12))
        ttk.Label(row2, text="using:").pack(side="left")
        ttk.Combobox(row2, textvariable=self.algorithm_var, state="readonly", width=15,
                     values=list(SORT_ALGORITHMS)).pack(side="left", padx=(6, 0))
        self.count_label = ttk.Label(row2, text="", style="Muted.TLabel")
        self.count_label.pack(side="right")

        # Anything that changes the list refreshes the table straight away.
        for variable in (self.search_var, self.filter_subject_var, self.filter_priority_var,
                         self.filter_status_var, self.sort_var, self.algorithm_var):
            variable.trace_add("write", lambda *args: self.refresh_table())

    def _build_table(self):
        columns = [("id", "ID", 45, "center"), ("name", "Topic", 170, "w"),
                   ("subject", "Subject", 160, "w"), ("minutes", "Minutes", 70, "e"),
                   ("priority", "Priority", 80, "center"), ("deadline", "Deadline", 160, "center"),
                   ("status", "Status", 90, "center"), ("created", "Created", 90, "center")]
        container, self.tree = styles.make_table(self, columns, height=10)
        container.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    # ------------------------------------------------------------------
    # Showing data
    # ------------------------------------------------------------------
    def refresh(self):
        """Called by the main window every time this page is opened."""
        self._load_subject_lists()
        self.refresh_table()

    def _load_subject_lists(self):
        """Reload the subject drop-downs (a subject may have been added or deleted)."""
        subjects = self.subjects.list_subjects()
        self.subject_ids = {}
        for subject in subjects:
            self.subject_ids[subject["subject_name"]] = subject["subject_id"]
        names = list(self.subject_ids)

        self.subject_combo.config(values=names)
        if self.subject_var.get() not in self.subject_ids:
            self.subject_var.set(names[0] if names else "")

        self.filter_subject_combo.config(values=[ALL_SUBJECTS] + names)
        if self.filter_subject_var.get() not in self.subject_ids:
            self.filter_subject_var.set(ALL_SUBJECTS)

    def _current_filters(self):
        """The filter choices as arguments for TopicManager.list_topics()."""
        priority = self.filter_priority_var.get()
        status = self.filter_status_var.get()
        sort_by = self.sort_var.get()
        return {
            "subject_id": self.subject_ids.get(self.filter_subject_var.get()),
            "priority": None if priority == ALL_PRIORITIES else priority,
            "status": None if status == ALL_STATUSES else status,
            "keyword": self.search_var.get(),
            "sort_by": None if sort_by == DEFAULT_ORDER else sort_by,
            "algorithm": self.algorithm_var.get(),
        }

    def refresh_table(self):
        options = self._current_filters()
        topics = self.topics.list_topics(**options)

        rows = []
        ids = []
        tags = []
        total_minutes = 0
        for topic in topics:
            deadline = topic["deadline"] or "-"
            if self.topics.is_overdue(topic):
                deadline += "  (overdue)"
            rows.append((topic["topic_id"], topic["topic_name"], topic["subject_name"],
                         topic["estimated_duration"], topic["priority"], deadline,
                         topic["status"], topic["created_at"][:10]))
            ids.append(topic["topic_id"])
            tags.append(styles.row_tag(topic["priority"], topic["status"]))
            total_minutes += topic["estimated_duration"]
        styles.fill_table(self.tree, rows, ids=ids, tags=tags)

        # The line above the table on the right.
        if rows:
            text = str(len(rows)) + " topic(s), " + format_minutes(total_minutes) + " in total"
            if options["sort_by"]:
                text += "  |  sorted by " + options["sort_by"].lower() + " with " + options["algorithm"]
        elif not self.topics.list_topics():
            text = "No topics yet. Add your first topic above."
        else:
            text = "No topic matches the current search and filters."
        self.count_label.config(text=text)

        self._sync_selected_topic()

    def _sync_selected_topic(self):
        """Keep the edited topic highlighted and its Complete/Pending button correct."""
        if self.selected_id is None:
            return
        try:
            topic = self.topics.get_topic(self.selected_id)
        except DatabaseError:  # it was deleted
            self.clear_form()
            return
        self._set_toggle_text(topic["status"])
        if self.tree.exists(str(self.selected_id)):
            self.tree.selection_set(str(self.selected_id))

    # ------------------------------------------------------------------
    # The form
    # ------------------------------------------------------------------
    def _set_toggle_text(self, status):
        self.toggle_button.config(text="Mark Pending" if status == "Completed" else "Mark Completed")

    def _set_editing(self, editing):
        """Editing = a table row is loaded in the form (Add is off, the others are on)."""
        if editing:
            self.add_button.state(["disabled"])
            for button in (self.save_button, self.toggle_button, self.delete_button):
                button.state(["!disabled"])
            self.hint.config(text="Editing topic #" + str(self.selected_id))
        else:
            self.add_button.state(["!disabled"])
            for button in (self.save_button, self.toggle_button, self.delete_button):
                button.state(["disabled"])
            self._set_toggle_text("Pending")
            self.hint.config(text="Click a row to edit it")

    def clear_form(self):
        """Empty the fields. The chosen subject stays, so adding several topics is quick."""
        self.selected_id = None
        self.name_var.set("")
        self.duration_var.set("")
        self.deadline_var.set("")
        self.priority_var.set("Medium")
        self.tree.selection_remove(self.tree.selection())
        self._set_editing(False)
        self.name_entry.focus_set()

    def on_select(self, event=None):
        """A row was clicked: load it into the form."""
        topic_id = styles.selected_id(self.tree)
        if topic_id is None or topic_id == self.selected_id:
            return  # nothing selected, or this row is already in the form
        try:
            topic = self.topics.get_topic(topic_id)
        except DatabaseError as error:
            styles.show_error(error)
            self.refresh_table()
            return
        self.selected_id = topic_id
        self.subject_var.set(topic["subject_name"])
        self.name_var.set(topic["topic_name"])
        self.duration_var.set(str(topic["estimated_duration"]))
        self.priority_var.set(topic["priority"])
        self.deadline_var.set(topic["deadline"] or "")
        self._set_toggle_text(topic["status"])
        self._set_editing(True)

    def on_enter(self):
        """The Enter key does Save when editing, otherwise Add."""
        if self.selected_id is None:
            self.add_topic()
        else:
            self.save_changes()

    def reset_filters(self):
        self.search_var.set("")
        self.filter_subject_var.set(ALL_SUBJECTS)
        self.filter_priority_var.set(ALL_PRIORITIES)
        self.filter_status_var.set(ALL_STATUSES)
        self.sort_var.set(DEFAULT_ORDER)

    def _chosen_subject_id(self):
        """The subject picked in the form, or None (after showing a hint)."""
        subject_id = self.subject_ids.get(self.subject_var.get())
        if subject_id is None:
            styles.show_warning("Please choose a subject first.\n"
                                "If the list is empty, add a subject on the Subjects page.")
        return subject_id

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def add_topic(self):
        subject_id = self._chosen_subject_id()
        if subject_id is None:
            return
        try:
            self.topics.add_topic(subject_id, self.name_var.get(), self.duration_var.get(),
                                  self.priority_var.get(), self.deadline_var.get())
        except DatabaseError as error:
            styles.show_error(error)
            return
        styles.show_info("Topic added successfully.")
        self.clear_form()
        self.refresh_table()

    def save_changes(self):
        if self.selected_id is None:
            styles.show_warning("Click a topic in the table first.")
            return
        subject_id = self._chosen_subject_id()
        if subject_id is None:
            return
        try:
            self.topics.update_topic(self.selected_id, subject_id, self.name_var.get(),
                                     self.duration_var.get(), self.priority_var.get(),
                                     self.deadline_var.get())
        except DatabaseError as error:
            styles.show_error(error)
            return
        styles.show_info("Topic updated successfully.")
        self.refresh_table()

    def toggle_status(self):
        """Pending <-> Completed for the selected topic."""
        if self.selected_id is None:
            styles.show_warning("Click a topic in the table first.")
            return
        try:
            self.topics.toggle_status(self.selected_id)
        except DatabaseError as error:
            styles.show_error(error)
        self.refresh_table()

    def delete_topic(self):
        if self.selected_id is None:
            styles.show_warning("Click a topic in the table first.")
            return
        try:
            topic = self.topics.get_topic(self.selected_id)
        except DatabaseError as error:
            styles.show_error(error)
            self.refresh_table()
            return
        if not styles.ask_yes_no("Delete the topic '" + topic["topic_name"] + "'?\n\n"
                                 "Any study sessions saved for it will be deleted too."):
            return
        try:
            self.topics.delete_topic(self.selected_id)
        except DatabaseError as error:
            styles.show_error(error)
            return
        styles.show_info("Topic deleted.")
        self.clear_form()
        self.refresh_table()