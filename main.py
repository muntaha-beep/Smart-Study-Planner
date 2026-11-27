"""
main.py - starts the Smart Study Planner & Time Optimizer (Phase 5).

Run with:   python main.py

This file builds the main window (sidebar on the left, page area on the right)
and switches between pages. Each page lives in its own file inside ui/.
A page is created the first time you open it and refreshed every time you
come back to it, so the numbers on screen always match the database.

A page file must contain a class that:
    * is created as   PageClass(parent_frame, app)
    * has a method    refresh()   that reloads its data from the database
"""

import importlib
import sys
import tkinter as tk
import traceback
from tkinter import ttk

import database
from database import DatabaseError
from ui import styles

# (sidebar text, module file, class name). The order here is the sidebar order.
PAGES = [
    ("Dashboard", "ui.dashboard", "DashboardPage"),
    ("Subjects", "ui.subjects_page", "SubjectsPage"),
    ("Study Topics", "ui.topics_page", "TopicsPage"),
    ("Generate Study Plan", "ui.planner_page", "PlannerPage"),
    ("Study Schedule", "ui.schedule_page", "SchedulePage"),
    ("Progress Tracking", "ui.progress_page", "ProgressPage"),
    ("Algorithm Analysis", "ui.algorithm_page", "AlgorithmPage"),
    ("Settings", "ui.settings_page", "SettingsPage"),
]
BOTTOM_ITEMS = ("Settings",)  # shown at the bottom of the sidebar, above Exit


# ----------------------------------------------------------------------
# Pages shown when a real page is missing or broken
# ----------------------------------------------------------------------
class MessagePage(ttk.Frame):
    """A simple page with a title and a message. Has a do-nothing refresh()."""

    def __init__(self, parent, title, message):
        super().__init__(parent)
        styles.PageHeader(self, title).pack(anchor="w")
        card = styles.Card(self)
        card.pack(fill="x", pady=20)
        ttk.Label(card, text=message, style="Card.TLabel", wraplength=700, justify="left",
                  padding=20).pack(anchor="w")

    def refresh(self):
        pass


# ----------------------------------------------------------------------
# One sidebar menu entry
# ----------------------------------------------------------------------
class SidebarItem(tk.Frame):
    """Clickable text with a coloured bar on the left when it is the active page."""

    def __init__(self, parent, text, command):
        super().__init__(parent, bg=styles.SIDEBAR_BG, cursor="hand2")
        self.command = command
        self.active = False

        self.bar = tk.Frame(self, width=4, bg=styles.SIDEBAR_BG)
        self.bar.pack(side="left", fill="y")
        self.label = tk.Label(self, text=text, font=styles.FONT_SIDEBAR, fg=styles.SIDEBAR_FG,
                              bg=styles.SIDEBAR_BG, anchor="w", padx=18, pady=11)
        self.label.pack(side="left", fill="x", expand=True)

        for widget in (self, self.bar, self.label):
            widget.bind("<Enter>", lambda e: self._paint(hover=True))
            widget.bind("<Leave>", lambda e: self._paint(hover=False))
            widget.bind("<Button-1>", lambda e: self.command())

    def _paint(self, hover=False):
        if self.active:
            background, bar, font = styles.SIDEBAR_HOVER, styles.PRIMARY, styles.FONT_SIDEBAR + ("bold",)
        elif hover:
            background, bar, font = styles.SIDEBAR_HOVER, styles.SIDEBAR_HOVER, styles.FONT_SIDEBAR
        else:
            background, bar, font = styles.SIDEBAR_BG, styles.SIDEBAR_BG, styles.FONT_SIDEBAR
        self.config(bg=background)
        self.bar.config(bg=bar)
        self.label.config(bg=background, font=font)

    def set_active(self, active):
        self.active = active
        self._paint()


# ----------------------------------------------------------------------
# The application window
# ----------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        styles.apply_styles(self)
        self.title(styles.APP_TITLE)
        styles.center_window(self, 1200, 740)
        self.minsize(1000, 620)  # the window can be resized, but not made unusably small

        self.items = {}   # sidebar text -> SidebarItem
        self.pages = {}   # sidebar text -> page (created on first visit)
        self.current = None

        self._build_sidebar()
        self.content = ttk.Frame(self, padding=(28, 22, 28, 18))
        self.content.pack(side="left", fill="both", expand=True)
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        # Keyboard shortcuts: Ctrl+1 ... Ctrl+7 open the first seven pages.
        for number, (name, _, _) in enumerate(PAGES[:7], start=1):
            self.bind("<Control-Key-" + str(number) + ">", lambda e, n=name: self.show_page(n))
        self.protocol("WM_DELETE_WINDOW", self.exit_app)

        self.show_page("Dashboard")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_sidebar(self):
        sidebar = tk.Frame(self, bg=styles.SIDEBAR_BG, width=235)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Smart Study\nPlanner", font=(styles.FONT_FAMILY, 17, "bold"),
                 fg="white", bg=styles.SIDEBAR_BG, justify="left", anchor="w",
                 padx=22, pady=22).pack(fill="x")
        tk.Label(sidebar, text="& Time Optimizer", font=styles.FONT_SMALL,
                 fg=styles.SIDEBAR_MUTED, bg=styles.SIDEBAR_BG, anchor="w",
                 padx=22).pack(fill="x", pady=(0, 18))

        # Exit and Settings at the bottom (packed first so they stay at the bottom).
        exit_item = SidebarItem(sidebar, "Exit", self.exit_app)
        exit_item.pack(side="bottom", fill="x", pady=(0, 14))
        for name in reversed(BOTTOM_ITEMS):
            self._add_item(sidebar, name, side="bottom")

        for name, _, _ in PAGES:
            if name not in BOTTOM_ITEMS:
                self._add_item(sidebar, name, side="top")

    def _add_item(self, sidebar, name, side):
        item = SidebarItem(sidebar, name, lambda n=name: self.show_page(n))
        item.pack(side=side, fill="x")
        self.items[name] = item

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------
    def _create_page(self, name):
        """Load the page class for this sidebar entry (or a message page if it can't)."""
        for page_name, module_name, class_name in PAGES:
            if page_name == name:
                break

        try:
            module = importlib.import_module(module_name)
            page_class = getattr(module, class_name)
        except ModuleNotFoundError as error:
            if error.name == module_name:  # the page file does not exist
                return MessagePage(self.content, name, "This page is built in a later step "
                                   "(" + module_name.replace(".", "/") + ".py).")
            return self._error_page(name, error)
        except AttributeError:  # the file exists but is still empty
            return MessagePage(self.content, name, "This page is built in a later step "
                               "(" + module_name.replace(".", "/") + ".py).")
        except Exception as error:
            return self._error_page(name, error)

        try:
            return page_class(self.content, self)
        except Exception as error:
            return self._error_page(name, error)

    def _error_page(self, name, error):
        traceback.print_exc()  # full details go to the terminal for debugging
        return MessagePage(self.content, name, "This page could not be opened:\n\n"
                           + type(error).__name__ + ": " + str(error)
                           + "\n\nThe full error is shown in the terminal.")

    def show_page(self, name):
        """Open a page by its sidebar text and refresh its data."""
        if name not in self.pages:
            page = self._create_page(name)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page
        page = self.pages[name]
        page.tkraise()

        for item_name, item in self.items.items():
            item.set_active(item_name == name)
        self.current = name

        try:
            page.refresh()
        except DatabaseError as error:
            styles.show_error(error)

    def refresh_pages(self):
        """Reload every page that has been opened (after data changed somewhere)."""
        for page in self.pages.values():
            try:
                page.refresh()
            except DatabaseError as error:
                styles.show_error(error)

    def exit_app(self):
        if styles.ask_yes_no("Do you want to exit the application?"):
            self.destroy()

    def report_callback_exception(self, exc_type, exc_value, exc_traceback):
        """Safety net: a bug inside a button click shows a message instead of failing silently."""
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        if isinstance(exc_value, DatabaseError):
            styles.show_error(exc_value)
        else:
            styles.show_error("Something unexpected went wrong:\n" + str(exc_value)
                              + "\n\nThe details are in the terminal.")


def main():
    # Sharper text on high-resolution Windows screens (ignored elsewhere).
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    try:
        database.init_db()  # creates study_planner.db and the tables if needed
    except DatabaseError as error:
        print("Could not open the database:", error)
        sys.exit(1)

    App().mainloop()


if __name__ == "__main__":
    main()