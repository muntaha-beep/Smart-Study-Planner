"""
progress_page.py - the Progress Tracking page (Phase 5).

Shows how much of the study work is done: overall numbers, a ring chart and a
progress bar for every subject. Every number is calculated from the real
topics and sessions in the database (ProgressTracker); nothing is hard-coded.
"""

import tkinter as tk
from tkinter import ttk

from modules.progress_tracker import ProgressTracker, format_minutes
from ui import styles

TRACK_COLOR = "#e5e8f0"


class SubjectProgressCard(styles.Card):
    """One subject: its name, a progress bar and the numbers behind it."""

    def __init__(self, parent, row):
        super().__init__(parent)
        inner = ttk.Frame(self, style="Card.TFrame", padding=(14, 10))
        inner.pack(fill="x")

        top = ttk.Frame(inner, style="Card.TFrame")
        top.pack(fill="x")
        name = row["subject_name"]
        if row["course_code"]:
            name += "  (" + row["course_code"] + ")"
        ttk.Label(top, text=name, style="Card.TLabel", font=styles.FONT_BOLD).pack(side="left")
        ttk.Label(top, text=str(row["completed_topics"]) + " of " + str(row["total_topics"])
                  + " topics", style="Card.TLabel").pack(side="right")

        bar_style = ("Success.Horizontal.TProgressbar" if row["total_topics"] and row["percent"] >= 100
                     else "Horizontal.TProgressbar")
        ttk.Progressbar(inner, orient="horizontal", mode="determinate", maximum=100,
                        value=row["percent"], style=bar_style).pack(fill="x", pady=(8, 4))

        if row["total_topics"] == 0:
            detail = "No topics yet - add some on the Study Topics page."
        else:
            detail = (str(row["percent"]) + "% done   |   " + str(row["pending_topics"])
                      + " pending   |   " + format_minutes(row["completed_minutes"]) + " of "
                      + format_minutes(row["total_minutes"]) + " topic time completed")
        ttk.Label(inner, text=detail, style="CardMuted.TLabel").pack(anchor="w")


class ProgressPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.tracker = ProgressTracker()

        styles.PageHeader(self, "Progress Tracking",
                          "How much of your study work is done (calculated from your real records)"
                          ).pack(anchor="w")
        self._build_cards()
        self._build_body()

    # ------------------------------------------------------------------
    # Building the page
    # ------------------------------------------------------------------
    def _build_cards(self):
        cards = ttk.Frame(self)
        cards.pack(fill="x", pady=(14, 12))
        self.overall_card = styles.StatCard(cards, "Overall progress", styles.PRIMARY)
        self.completed_card = styles.StatCard(cards, "Completed topics", styles.SUCCESS)
        self.pending_card = styles.StatCard(cards, "Pending topics", styles.WARNING)
        self.time_card = styles.StatCard(cards, "Study time done", styles.PURPLE)
        for column, card in enumerate([self.overall_card, self.completed_card,
                                       self.pending_card, self.time_card]):
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 10, 0))
            cards.columnconfigure(column, weight=1)

    def _build_body(self):
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Left: ring chart and legend
        left = styles.Card(body)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        inner = ttk.Frame(left, style="Card.TFrame", padding=16)
        inner.pack(fill="both", expand=True)
        ttk.Label(inner, text="Topics completed", style="Card.TLabel",
                  font=styles.FONT_BOLD).pack(anchor="w")
        self.donut = tk.Canvas(inner, width=180, height=180, bg=styles.CARD_BG,
                               highlightthickness=0)
        self.donut.pack(pady=10)
        self.legend_done = tk.Label(inner, text="", bg=styles.CARD_BG, fg=styles.TEXT,
                                    font=styles.FONT_BASE, anchor="w")
        self.legend_done.pack(fill="x")
        self.legend_pending = tk.Label(inner, text="", bg=styles.CARD_BG, fg=styles.TEXT,
                                       font=styles.FONT_BASE, anchor="w")
        self.legend_pending.pack(fill="x")
        self.sessions_label = ttk.Label(inner, text="", style="CardMuted.TLabel", wraplength=190,
                                        justify="left")
        self.sessions_label.pack(anchor="w", pady=(12, 0))

        # Right: one card per subject (scrolls when there are many)
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        ttk.Label(right, text="Subject-wise progress", style="Heading.TLabel").pack(anchor="w",
                                                                                     pady=(0, 8))
        self.subject_area = styles.ScrollableFrame(right)
        self.subject_area.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Showing data
    # ------------------------------------------------------------------
    def refresh(self):
        """Called by the main window every time this page is opened."""
        overall = self.tracker.overall_progress()
        subjects = self.tracker.subject_progress()

        self.overall_card.set(str(overall["completion_percent"]) + "%",
                              str(overall["completed_topics"]) + " of "
                              + str(overall["total_topics"]) + " topics")
        self.completed_card.set(overall["completed_topics"],
                                format_minutes(overall["completed_minutes"]) + " of topic time")
        self.pending_card.set(overall["pending_topics"],
                              format_minutes(overall["pending_minutes"]) + " still to study")
        self.time_card.set(format_minutes(overall["studied_minutes"]),
                           str(overall["completed_sessions"]) + " of "
                           + str(overall["total_sessions"]) + " session(s) completed")

        self._draw_donut(overall)
        self.legend_done.config(text="\u25CF Completed: " + str(overall["completed_topics"]),
                                fg=styles.SUCCESS)
        self.legend_pending.config(text="\u25CF Pending: " + str(overall["pending_topics"]),
                                   fg=styles.MUTED)
        self.sessions_label.config(text="Sessions: " + str(overall["completed_sessions"])
                                   + " completed, " + str(overall["pending_sessions"]) + " pending")

        self._fill_subjects(subjects)

    def _draw_donut(self, overall):
        """A ring that is green for the completed share of all topics."""
        canvas = self.donut
        canvas.delete("all")
        box = (18, 18, 162, 162)
        canvas.create_oval(*box, outline=TRACK_COLOR, width=22)  # the empty ring

        total = overall["total_topics"]
        done = overall["completed_topics"]
        if total > 0 and done >= total:
            canvas.create_oval(*box, outline=styles.SUCCESS, width=22)
        elif total > 0 and done > 0:
            canvas.create_arc(*box, start=90, extent=-360 * done / total, style="arc",
                              outline=styles.SUCCESS, width=22)

        canvas.create_text(90, 82, text=str(overall["completion_percent"]) + "%",
                           font=(styles.FONT_FAMILY, 22, "bold"), fill=styles.TEXT)
        canvas.create_text(90, 108, text="completed", font=styles.FONT_SMALL, fill=styles.MUTED)

    def _fill_subjects(self, subjects):
        body = self.subject_area.body
        for child in body.winfo_children():
            child.destroy()

        if not subjects:
            ttk.Label(body, text="No subjects yet. Add subjects and topics to see your progress.",
                      style="Subtitle.TLabel").pack(anchor="w", pady=10)
            return
        for row in subjects:
            SubjectProgressCard(body, row).pack(fill="x", pady=(0, 8))