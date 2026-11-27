"""
styles.py - colours, fonts and small reusable widgets for every page (Phase 5).

Keeping all of this in one place gives the whole application the same look.
Run  python -m ui.styles  to see a preview window of everything defined here.
"""

import tkinter as tk
from tkinter import ttk, messagebox

APP_TITLE = "Smart Study Planner & Time Optimizer"

# ----------------------------------------------------------------------
# Colours
# ----------------------------------------------------------------------
SIDEBAR_BG = "#1f2a44"
SIDEBAR_HOVER = "#2c3a5c"
SIDEBAR_FG = "#e8ecf4"
SIDEBAR_MUTED = "#8c9abb"

BG = "#f4f6fb"          # page background
CARD_BG = "#ffffff"     # cards and tables
BORDER = "#e1e5ee"
TEXT = "#1f2937"
MUTED = "#6b7280"

PRIMARY = "#3b82f6"
PRIMARY_DARK = "#2563eb"
SUCCESS = "#16a34a"
SUCCESS_DARK = "#15803d"
WARNING = "#f59e0b"
DANGER = "#dc2626"
DANGER_DARK = "#b91c1c"
PURPLE = "#8b5cf6"
TEAL = "#0d9488"

# Light row colours for priorities in tables.
HIGH_BG = "#fee2e2"
MEDIUM_BG = "#fef3c7"
LOW_BG = "#dcfce7"
STRIPE_BG = "#f8f9fc"

# ----------------------------------------------------------------------
# Fonts (if Segoe UI is missing, Tkinter quietly uses a default font)
# ----------------------------------------------------------------------
FONT_FAMILY = "Segoe UI"
FONT_BASE = (FONT_FAMILY, 10)
FONT_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_TITLE = (FONT_FAMILY, 20, "bold")
FONT_HEADING = (FONT_FAMILY, 13, "bold")
FONT_CARD_VALUE = (FONT_FAMILY, 24, "bold")
FONT_SIDEBAR = (FONT_FAMILY, 11)
FONT_MONO = ("Consolas", 10)  # for algorithm step-by-step text


# ----------------------------------------------------------------------
# Apply the look to every ttk widget
# ----------------------------------------------------------------------
def apply_styles(root):
    """Call once, right after creating the main window."""
    style = ttk.Style(root)
    style.theme_use("clam")  # the "clam" theme lets us change colours
    root.configure(bg=BG)

    style.configure(".", font=FONT_BASE, background=BG, foreground=TEXT)

    # Frames and labels
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD_BG)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT)
    style.configure("Title.TLabel", font=FONT_TITLE, foreground=TEXT)
    style.configure("Heading.TLabel", font=FONT_HEADING)
    style.configure("Subtitle.TLabel", foreground=MUTED)
    style.configure("Muted.TLabel", foreground=MUTED, font=FONT_SMALL)
    style.configure("CardMuted.TLabel", background=CARD_BG, foreground=MUTED, font=FONT_SMALL)
    style.configure("Bold.TLabel", font=FONT_BOLD)

    # Buttons: default (grey) plus Primary / Success / Danger
    style.configure("TButton", font=FONT_BASE, padding=(12, 6), background="#e9edf5",
                    foreground=TEXT, borderwidth=0, focusthickness=0)
    style.map("TButton", background=[("active", "#d9deea"), ("disabled", "#f0f2f7")],
              foreground=[("disabled", "#a0a7b5")])
    for name, normal, hover in [("Primary", PRIMARY, PRIMARY_DARK),
                                ("Success", SUCCESS, SUCCESS_DARK),
                                ("Danger", DANGER, DANGER_DARK)]:
        style.configure(name + ".TButton", background=normal, foreground="white",
                        font=FONT_BOLD, padding=(14, 7), borderwidth=0, focusthickness=0)
        style.map(name + ".TButton", background=[("active", hover), ("disabled", "#b6bcc9")],
                  foreground=[("disabled", "#f3f4f6")])

    # Entry, Combobox, Spinbox
    for widget in ("TEntry", "TCombobox", "TSpinbox"):
        style.configure(widget, fieldbackground="white", background="white",
                        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                        padding=5)
    style.map("TCombobox", fieldbackground=[("readonly", "white")],
              selectbackground=[("readonly", "white")],
              selectforeground=[("readonly", TEXT)])

    # Table (Treeview)
    style.configure("Treeview", background="white", fieldbackground="white",
                    foreground=TEXT, rowheight=28, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, borderwidth=1, font=FONT_BASE)
    style.configure("Treeview.Heading", background="#eef1f8", foreground=TEXT,
                    font=FONT_BOLD, relief="flat", padding=(6, 7))
    style.map("Treeview", background=[("selected", PRIMARY)],
              foreground=[("selected", "white")])
    style.map("Treeview.Heading", background=[("active", "#e1e6f2")])

    # Progress bars
    style.configure("Horizontal.TProgressbar", troughcolor="#e5e8f0", background=PRIMARY,
                    thickness=14, bordercolor="#e5e8f0", lightcolor=PRIMARY, darkcolor=PRIMARY)
    style.configure("Success.Horizontal.TProgressbar", troughcolor="#e5e8f0",
                    background=SUCCESS, thickness=14, bordercolor="#e5e8f0",
                    lightcolor=SUCCESS, darkcolor=SUCCESS)

    # Tabs and group boxes
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(16, 8), font=FONT_BASE, background="#e4e8f2")
    style.map("TNotebook.Tab", background=[("selected", "white")],
              font=[("selected", FONT_BOLD)])
    style.configure("TLabelframe", background=BG, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=BG, foreground=TEXT, font=FONT_BOLD)
    style.configure("TRadiobutton", background=BG)
    style.configure("TCheckbutton", background=BG)

    # Drop-down list of a Combobox uses classic Tk options
    root.option_add("*TCombobox*Listbox.font", FONT_BASE)
    root.option_add("*TCombobox*Listbox.selectBackground", PRIMARY)


def center_window(window, width, height):
    """Open a window in the middle of the screen."""
    x = max((window.winfo_screenwidth() - width) // 2, 0)
    y = max((window.winfo_screenheight() - height) // 2 - 20, 0)
    window.geometry(str(width) + "x" + str(height) + "+" + str(x) + "+" + str(y))


# ----------------------------------------------------------------------
# Message boxes (one place, so every message looks the same)
# ----------------------------------------------------------------------
def show_error(message):
    messagebox.showerror(APP_TITLE, str(message))


def show_info(message):
    messagebox.showinfo(APP_TITLE, str(message))


def show_warning(message):
    messagebox.showwarning(APP_TITLE, str(message))


def ask_yes_no(message):
    """Returns True if the user clicked Yes."""
    return messagebox.askyesno(APP_TITLE, str(message))


# ----------------------------------------------------------------------
# Reusable widgets
# ----------------------------------------------------------------------
class Card(tk.Frame):
    """A white box with a thin border. Put widgets inside it."""

    def __init__(self, parent, **options):
        super().__init__(parent, bg=CARD_BG, highlightthickness=1,
                         highlightbackground=BORDER, highlightcolor=BORDER, **options)


class StatCard(Card):
    """A dashboard card: coloured edge, small title, big number, small note."""

    def __init__(self, parent, title, accent=PRIMARY):
        super().__init__(parent)
        tk.Frame(self, bg=accent, width=6).pack(side="left", fill="y")
        body = tk.Frame(self, bg=CARD_BG)
        body.pack(side="left", fill="both", expand=True, padx=16, pady=12)
        ttk.Label(body, text=title, style="CardMuted.TLabel").pack(anchor="w")
        self.value_label = tk.Label(body, text="0", font=FONT_CARD_VALUE, bg=CARD_BG, fg=TEXT)
        self.value_label.pack(anchor="w")
        self.note_label = ttk.Label(body, text="", style="CardMuted.TLabel")
        self.note_label.pack(anchor="w")

    def set(self, value, note=""):
        self.value_label.config(text=str(value))
        self.note_label.config(text=note)


class PageHeader(ttk.Frame):
    """Big page title with a grey sentence under it."""

    def __init__(self, parent, title, subtitle=""):
        super().__init__(parent)
        ttk.Label(self, text=title, style="Title.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(self, text=subtitle, style="Subtitle.TLabel").pack(anchor="w", pady=(2, 0))


class ProgressRow(ttk.Frame):
    """One line: a name, a progress bar and a text such as '3/5 (60%)'."""

    def __init__(self, parent, label, label_width=24):
        super().__init__(parent, style="Card.TFrame")
        self.name = ttk.Label(self, text=label, style="Card.TLabel", width=label_width,
                              anchor="w")
        self.name.pack(side="left", padx=(0, 10))
        self.bar = ttk.Progressbar(self, orient="horizontal", mode="determinate",
                                   maximum=100, length=260)
        self.bar.pack(side="left", fill="x", expand=True)
        self.text = ttk.Label(self, text="", style="Card.TLabel", width=22, anchor="e")
        self.text.pack(side="left", padx=(10, 0))

    def set(self, percent, text=""):
        """percent: 0..100. The bar turns green when it is full."""
        self.bar.config(value=percent,
                        style="Success.Horizontal.TProgressbar" if percent >= 100
                        else "Horizontal.TProgressbar")
        self.text.config(text=text)


class ScrollableFrame(ttk.Frame):
    """A frame that scrolls. Put your widgets inside  .body"""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.body = ttk.Frame(self.canvas)
        self._window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>",
                       lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfigure(self._window, width=e.width))

        # Mouse wheel only scrolls while the pointer is over this frame.
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

    def _bind_wheel(self, _event):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)      # Windows / macOS
        self.canvas.bind_all("<Button-4>", self._on_wheel)        # Linux up
        self.canvas.bind_all("<Button-5>", self._on_wheel)        # Linux down

    def _unbind_wheel(self, _event):
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.unbind_all(sequence)

    def _on_wheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-event.delta / 120), "units")


# ----------------------------------------------------------------------
# Tables
# ----------------------------------------------------------------------
def make_table(parent, columns, height=10):
    """
    Build a table (Treeview) with scroll bars.

    columns : list of (column_id, heading_text, width_in_pixels, alignment)
              alignment is "w" (left), "center" or "e" (right)
    Returns (container, tree). Pack or grid the container; use the tree to
    fill and read the table.
    """
    container = ttk.Frame(parent)
    ids = [column[0] for column in columns]
    tree = ttk.Treeview(container, columns=ids, show="headings", height=height,
                        selectmode="browse")
    for column_id, heading, width, anchor in columns:
        tree.heading(column_id, text=heading, anchor=anchor)
        tree.column(column_id, width=width, minwidth=40, anchor=anchor)

    vertical = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
    horizontal = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    container.rowconfigure(0, weight=1)
    container.columnconfigure(0, weight=1)

    # Row colours
    tree.tag_configure("odd", background="white")
    tree.tag_configure("even", background=STRIPE_BG)
    tree.tag_configure("High", background=HIGH_BG)
    tree.tag_configure("Medium", background=MEDIUM_BG)
    tree.tag_configure("Low", background=LOW_BG)
    tree.tag_configure("Completed", foreground=MUTED, background="#f1f3f7")
    tree.tag_configure("Overdue", foreground=DANGER)
    return container, tree


def fill_table(tree, rows, ids=None, tags=None):
    """
    Replace everything in the table.

    rows : list of tuples, one tuple per row
    ids  : optional list of record ids (same length as rows); read one back
           later with selected_id(tree)
    tags : optional list with a tag name per row ("High", "Completed", ...).
           Without tags the rows get alternating stripes.
    """
    tree.delete(*tree.get_children())
    for index, row in enumerate(rows):
        if tags is not None and tags[index]:
            tag = tags[index]
        else:
            tag = "even" if index % 2 else "odd"
        iid = str(ids[index]) if ids is not None else None
        tree.insert("", "end", iid=iid, values=row, tags=(tag,))


def selected_id(tree):
    """The id of the selected row as a number, or None if nothing is selected."""
    selection = tree.selection()
    if not selection:
        return None
    try:
        return int(selection[0])
    except ValueError:
        return None


def row_tag(priority=None, status=None):
    """Which colour tag a topic row should get."""
    if status == "Completed":
        return "Completed"
    return priority  # "High", "Medium", "Low" (or None)


# ----------------------------------------------------------------------
# Preview: run with   python -m ui.styles
# ----------------------------------------------------------------------
def build_demo(root):
    """Fill a window with one example of everything (used by the preview)."""
    apply_styles(root)
    root.title(APP_TITLE + " - style preview")

    page = ttk.Frame(root, padding=24)
    page.pack(fill="both", expand=True)
    PageHeader(page, "Style preview", "Colours, cards, buttons, tables and progress bars").pack(anchor="w")

    cards = ttk.Frame(page)
    cards.pack(fill="x", pady=16)
    specs = [("Subjects", 5, "courses", PRIMARY), ("Topics", 24, "18 pending", PURPLE),
             ("Completed", 6, "25% done", SUCCESS), ("Study time", "12.5 h", "estimated", WARNING)]
    for column, (title, value, note, accent) in enumerate(specs):
        card = StatCard(cards, title, accent)
        card.set(value, note)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 12, 0))
        cards.columnconfigure(column, weight=1)

    buttons = ttk.Frame(page)
    buttons.pack(fill="x", pady=(0, 12))
    ttk.Button(buttons, text="Add", style="Primary.TButton").pack(side="left", padx=(0, 8))
    ttk.Button(buttons, text="Complete", style="Success.TButton").pack(side="left", padx=(0, 8))
    ttk.Button(buttons, text="Delete", style="Danger.TButton").pack(side="left", padx=(0, 8))
    ttk.Button(buttons, text="Cancel").pack(side="left", padx=(0, 16))
    ttk.Entry(buttons, width=18).pack(side="left", padx=(0, 8))
    combo = ttk.Combobox(buttons, values=["High", "Medium", "Low"], state="readonly", width=10)
    combo.set("High")
    combo.pack(side="left")

    container, tree = make_table(page, [("topic", "Topic", 180, "w"), ("subject", "Subject", 180, "w"),
                                        ("minutes", "Minutes", 80, "e"), ("priority", "Priority", 90, "center"),
                                        ("status", "Status", 100, "center")], height=6)
    container.pack(fill="x")
    sample = [("Trees", "Data Structures", 60, "High", "Pending"),
              ("SQL", "DBMS", 45, "Medium", "Pending"),
              ("Arrays", "Data Structures", 30, "Low", "Pending"),
              ("Joins", "DBMS", 50, "High", "Completed")]
    fill_table(tree, sample, ids=[1, 2, 3, 4],
               tags=[row_tag(r[3], r[4]) for r in sample])

    box = Card(page)
    box.pack(fill="x", pady=16)
    inner = ttk.Frame(box, style="Card.TFrame", padding=14)
    inner.pack(fill="x")
    for label, percent_value, text in [("Data Structures", 33, "1/3 (33.3%)"), ("DBMS", 75, "3/4 (75.0%)"),
                                       ("Operating Systems", 100, "2/2 (100%)")]:
        row = ProgressRow(inner, label)
        row.set(percent_value, text)
        row.pack(fill="x", pady=4)
    return root


if __name__ == "__main__":
    window = tk.Tk()
    build_demo(window)
    center_window(window, 900, 720)
    window.mainloop()