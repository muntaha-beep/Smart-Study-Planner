"""
subjects_page.py - the Subjects page (Phase 5).

Add, edit, delete and search subjects. This page only talks to SubjectManager;
it never writes SQL. Every problem comes back as a DatabaseError, which is
shown in an error box.
"""

import tkinter as tk
from tkinter import ttk

from database import DatabaseError
from modules.subject_manager import SubjectManager
from ui import styles


class SubjectsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.manager = SubjectManager()
        self.selected_id = None  # id of the subject being edited (None = adding a new one)

        styles.PageHeader(self, "Subjects",
                          "Add, edit, search and delete your academic subjects").pack(anchor="w")
        self._build_form()
        self._build_table()
        self._set_editing(False)

    # ------------------------------------------------------------------
    # Building the page
    # ------------------------------------------------------------------
    def _build_form(self):
        card = styles.Card(self)
        card.pack(fill="x", pady=(16, 14))
        form = ttk.Frame(card, style="Card.TFrame", padding=16)
        form.pack(fill="x")
        form.columnconfigure(2, weight=1)

        self.name_var = tk.StringVar()
        self.code_var = tk.StringVar()
        self.desc_var = tk.StringVar()

        ttk.Label(form, text="Subject name *", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(form, text="Course code (optional)", style="Card.TLabel").grid(
            row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Label(form, text="Description (optional)", style="Card.TLabel").grid(
            row=0, column=2, sticky="w", padx=(12, 0))

        self.name_entry = ttk.Entry(form, textvariable=self.name_var, width=34)
        self.name_entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.code_entry = ttk.Entry(form, textvariable=self.code_var, width=16)
        self.code_entry.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(4, 0))
        self.desc_entry = ttk.Entry(form, textvariable=self.desc_var)
        self.desc_entry.grid(row=1, column=2, sticky="ew", padx=(12, 0), pady=(4, 0))

        for entry in (self.name_entry, self.code_entry, self.desc_entry):
            entry.bind("<Return>", lambda e: self.on_enter())
            entry.bind("<Escape>", lambda e: self.clear_form())

        buttons = ttk.Frame(form, style="Card.TFrame")
        buttons.grid(row=2, column=0, columnspan=3, sticky="w", pady=(14, 0))
        self.add_button = ttk.Button(buttons, text="Add Subject", style="Primary.TButton",
                                     command=self.add_subject)
        self.add_button.pack(side="left", padx=(0, 8))
        self.save_button = ttk.Button(buttons, text="Save Changes", style="Success.TButton",
                                      command=self.save_changes)
        self.save_button.pack(side="left", padx=(0, 8))
        self.delete_button = ttk.Button(buttons, text="Delete", style="Danger.TButton",
                                        command=self.delete_subject)
        self.delete_button.pack(side="left", padx=(0, 8))
        self.clear_button = ttk.Button(buttons, text="Clear", command=self.clear_form)
        self.clear_button.pack(side="left", padx=(0, 16))
        self.hint = ttk.Label(buttons, text="", style="CardMuted.TLabel")
        self.hint.pack(side="left")

    def _build_table(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Label(bar, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(bar, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(8, 8))
        ttk.Button(bar, text="Clear search", command=lambda: self.search_var.set("")).pack(side="left")
        self.count_label = ttk.Label(bar, text="", style="Muted.TLabel")
        self.count_label.pack(side="right")
        # The table updates as you type.
        self.search_var.trace_add("write", lambda *args: self.refresh_table())

        columns = [("id", "ID", 50, "center"), ("name", "Subject", 260, "w"),
                   ("code", "Course Code", 110, "w"), ("topics", "Topics", 70, "center"),
                   ("done", "Completed", 90, "center"), ("desc", "Description", 340, "w")]
        container, self.tree = styles.make_table(self, columns, height=12)
        container.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    # ------------------------------------------------------------------
    # Showing data
    # ------------------------------------------------------------------
    def refresh(self):
        """Called by the main window every time this page is opened."""
        self.refresh_table()

    def refresh_table(self):
        keyword = self.search_var.get()
        subjects = self.manager.list_subjects_with_counts(keyword)

        rows = []
        ids = []
        for subject in subjects:
            rows.append((subject["subject_id"], subject["subject_name"],
                         subject["course_code"] or "-", subject["topic_count"],
                         str(subject["completed_count"]) + "/" + str(subject["topic_count"]),
                         subject["description"] or ""))
            ids.append(subject["subject_id"])
        styles.fill_table(self.tree, rows, ids=ids)

        if rows:
            self.count_label.config(text=str(len(rows)) + " subject(s)")
        elif keyword.strip():
            self.count_label.config(text="No subject matches your search.")
        else:
            self.count_label.config(text="No subjects yet. Add your first subject above.")

        # Keep the edited row highlighted if it is still in the list.
        if self.selected_id is not None:
            if self.tree.exists(str(self.selected_id)):
                self.tree.selection_set(str(self.selected_id))
            else:
                try:  # hidden by the search, or really deleted?
                    self.manager.get_subject(self.selected_id)
                except DatabaseError:
                    self.clear_form()

    # ------------------------------------------------------------------
    # The form
    # ------------------------------------------------------------------
    def _set_editing(self, editing):
        """Editing = a table row is loaded in the form (Add is off, Save/Delete are on)."""
        if editing:
            self.add_button.state(["disabled"])
            self.save_button.state(["!disabled"])
            self.delete_button.state(["!disabled"])
            self.hint.config(text="Editing subject #" + str(self.selected_id)
                             + ". Click Clear to add a new one instead.")
        else:
            self.add_button.state(["!disabled"])
            self.save_button.state(["disabled"])
            self.delete_button.state(["disabled"])
            self.hint.config(text="Fill in the form to add a subject, or click a row to edit it.")

    def clear_form(self):
        self.selected_id = None
        self.name_var.set("")
        self.code_var.set("")
        self.desc_var.set("")
        self.tree.selection_remove(self.tree.selection())
        self._set_editing(False)
        self.name_entry.focus_set()

    def on_select(self, event=None):
        """A row was clicked: load it into the form."""
        subject_id = styles.selected_id(self.tree)
        if subject_id is None or subject_id == self.selected_id:
            return  # nothing selected, or this row is already in the form
        try:
            subject = self.manager.get_subject(subject_id)
        except DatabaseError as error:
            styles.show_error(error)
            self.refresh_table()
            return
        self.selected_id = subject_id
        self.name_var.set(subject["subject_name"])
        self.code_var.set(subject["course_code"] or "")
        self.desc_var.set(subject["description"] or "")
        self._set_editing(True)

    def on_enter(self):
        """The Enter key does Save when editing, otherwise Add."""
        if self.selected_id is None:
            self.add_subject()
        else:
            self.save_changes()

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def add_subject(self):
        try:
            self.manager.add_subject(self.name_var.get(), self.code_var.get(), self.desc_var.get())
        except DatabaseError as error:
            styles.show_error(error)
            return
        styles.show_info("Subject added successfully.")
        self.clear_form()
        self.refresh_table()

    def save_changes(self):
        if self.selected_id is None:
            styles.show_warning("Click a subject in the table first.")
            return
        try:
            self.manager.update_subject(self.selected_id, self.name_var.get(),
                                        self.code_var.get(), self.desc_var.get())
        except DatabaseError as error:
            styles.show_error(error)
            return
        styles.show_info("Subject updated successfully.")
        self.refresh_table()

    def delete_subject(self):
        if self.selected_id is None:
            styles.show_warning("Click a subject in the table first.")
            return
        try:
            subject = self.manager.get_subject(self.selected_id)
            topic_count = self.manager.count_topics(self.selected_id)
        except DatabaseError as error:
            styles.show_error(error)
            self.refresh_table()
            return

        message = "Delete the subject '" + subject["subject_name"] + "'?"
        if topic_count > 0:
            message += ("\n\nThis will also delete its " + str(topic_count)
                        + " topic(s) and their study sessions.")
        if not styles.ask_yes_no(message):
            return
        try:
            self.manager.delete_subject(self.selected_id)
        except DatabaseError as error:
            styles.show_error(error)
            return
        styles.show_info("Subject deleted.")
        self.clear_form()
        self.refresh_table()