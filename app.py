"""
UniResolve - Campus Helpdesk & Complaint Management System
"Your Campus. Your Voice. Our Resolution."

Front end : Tkinter (Python's built-in GUI library)
Back end  : SQLite database (see database.py and schema.sql)

Run with:  python app.py
"""

import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, font as tkfont

import database as db

# ------------------------------------------------------------------ theme
DARK = "#173D2D"        # sidebar / brand panel
GREEN = "#238653"       # primary buttons, accents
GREEN_HOVER = "#1B6E43"
BG = "#F4F7F5"          # window background
CARD = "#FFFFFF"
BORDER = "#DDE5E0"
FIELD = "#F8FAF9"       # inside of text boxes
LIGHT = "#EEF3F0"       # table headers, hover
SELECT = "#DCEFE4"      # selected table row
TEXT = "#26352C"
MUTED = "#78857D"
SOFT = "#C4D6CC"        # light text on dark green
RED = "#D9534F"         # sign out / delete

STATUS_COLORS = {"Pending": "#E9A23B", "In Progress": "#397CC5", "Resolved": "#238653"}
PRIORITY_COLORS = {"High": "#D9534F", "Medium": "#E9A23B", "Low": "#78857D"}

FONT = "Segoe UI"       # replaced at start-up if not installed


def F(size=10, weight="normal"):
    return (FONT, size, weight)


# ------------------------------------------------------------------ small widget helpers

def button(parent, text, command, primary=True, danger=False, **kw):
    """
    A flat button that changes colour on hover.
    It is a Label that reacts to clicks, because macOS ignores colours on a normal tk.Button
    (it would show a grey button with white, unreadable text).
    """
    bg, fg, hover = (GREEN, "white", GREEN_HOVER) if primary else (CARD, TEXT, LIGHT)
    if danger:
        bg, fg, hover = (CARD, RED, "#FBEDEC")
    b = tk.Label(parent, text=text, bg=bg, fg=fg, cursor="hand2", font=F(10, "bold"),
                 padx=18, pady=8, highlightthickness=0 if primary else 1,
                 highlightbackground=BORDER, highlightcolor=BORDER, **kw)
    b.bind("<Button-1>", lambda e: command())
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def card(parent, **kw):
    return tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightcolor=BORDER,
                    highlightthickness=1, **kw)


def field_label(parent, text):
    return tk.Label(parent, text=text, bg=parent["bg"], fg=TEXT, font=F(9, "bold"), anchor="w")


def entry(parent, show=None):
    return tk.Entry(parent, font=F(10), relief="flat", bg=FIELD, fg=TEXT, show=show,
                    highlightthickness=1, highlightbackground=BORDER, highlightcolor=GREEN,
                    insertbackground=TEXT)


def dot_image(color, size=10):
    """Draw a small filled circle, used as the coloured status dot in tables."""
    img = tk.PhotoImage(width=size + 6, height=size)
    r = size / 2
    for y in range(size):
        for x in range(size):
            if (x - r + 0.5) ** 2 + (y - r + 0.5) ** 2 <= r * r:
                img.put(color, (x, y))
    return img


def nice_date(text):
    """'2026-11-12 14:40:00' -> '12 Nov 2026'"""
    return datetime.strptime(text[:10], "%Y-%m-%d").strftime("%d %b %Y")


def combo(parent, values, editable=False):
    c = ttk.Combobox(parent, values=values, font=F(10), state="normal" if editable else "readonly")
    c.set(values[0])
    return c


# ------------------------------------------------------------------ main application

class UniResolveApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("UniResolve - Campus Helpdesk & Complaint Management")
        self.geometry("1280x760")
        self.minsize(1200, 700)
        self.configure(bg=BG)

        self._setup_fonts_and_styles()
        db.init_db()                     # creates uniresolve.db on first run

        assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        self.logo_big = tk.PhotoImage(file=os.path.join(assets, "logo_login.png"))      # login screen
        self.logo_small = tk.PhotoImage(file=os.path.join(assets, "logo_sidebar.png"))  # sidebar
        self.iconphoto(True, tk.PhotoImage(file=os.path.join(assets, "logo_crest.png")).subsample(4))
        self.dots = {status: dot_image(color) for status, color in STATUS_COLORS.items()}

        self.user = None                 # the logged-in user (a database row)
        self.show_login()

    def _setup_fonts_and_styles(self):
        global FONT
        installed = set(tkfont.families())
        FONT = next((f for f in ("Segoe UI", "Inter", "Helvetica") if f in installed), "TkDefaultFont")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                        rowheight=34, font=F(10), borderwidth=0)
        style.configure("Treeview.Heading", background=LIGHT, foreground=MUTED,
                        font=F(9, "bold"), relief="flat", padding=(8, 8))
        style.map("Treeview", background=[("selected", SELECT)], foreground=[("selected", TEXT)])
        style.map("Treeview.Heading", background=[("active", LIGHT)])
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])   # no dark border
        style.configure("TCombobox", padding=6, arrowcolor=GREEN, bordercolor=BORDER,
                        lightcolor=BORDER, darkcolor=BORDER, background=CARD, arrowsize=14)
        style.map("TCombobox", fieldbackground=[("readonly", "white"), ("!readonly", "white")],
                  foreground=[("readonly", "black"), ("!readonly", "black")],
                  background=[("active", LIGHT), ("!active", CARD)],
                  bordercolor=[("focus", GREEN)], lightcolor=[("focus", GREEN)],
                  selectbackground=[("readonly", "white")], selectforeground=[("readonly", "black")])
        style.configure("Vertical.TScrollbar", background=LIGHT, troughcolor=CARD, bordercolor=CARD,
                        lightcolor=LIGHT, darkcolor=LIGHT, arrowcolor=MUTED, gripcount=0, arrowsize=12)
        self.option_add("*TCombobox*Listbox.font", F(10))
        self.option_add("*TCombobox*Listbox.background", "white")       # dropdown list
        self.option_add("*TCombobox*Listbox.foreground", "black")
        self.option_add("*TCombobox*Listbox.selectBackground", SELECT)
        self.option_add("*TCombobox*Listbox.selectForeground", "black")

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    # ============================================================== login & register

    def brand_panel(self):
        """Green panel on the left of the login and register screens."""
        panel = tk.Frame(self, bg=DARK, width=440)
        panel.pack(side="left", fill="y")
        panel.pack_propagate(False)

        inner = tk.Frame(panel, bg=DARK)
        inner.place(relx=0.5, rely=0.45, anchor="center")
        tk.Label(inner, image=self.logo_big, bg=DARK).pack()
        tk.Label(inner, text="Your Campus. Your Voice. Our Resolution.", bg=DARK, fg=SOFT,
                 font=F(11)).pack(pady=(16, 30))
        for line in ("Raise a campus complaint in under a minute",
                     "Track every ticket from Pending to Resolved",
                     "Admins update status and leave remarks"):
            row = tk.Frame(inner, bg=DARK)
            row.pack(anchor="w", pady=5)
            tk.Label(row, text="✓", bg=DARK, fg="#6FD39C", font=F(11, "bold")).pack(side="left")
            tk.Label(row, text=line, bg=DARK, fg="white", font=F(10)).pack(side="left", padx=10)

        tk.Label(panel, text="SRMIST  ·  Campus Helpdesk", bg=DARK, fg="#6E8F7E",
                 font=F(9)).pack(side="bottom", pady=20)

    def show_login(self, prefill=""):
        self.clear()
        self.user = None
        self.brand_panel()

        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        box = card(right, padx=40, pady=36)
        box.place(relx=0.5, rely=0.5, anchor="center", width=420)

        tk.Label(box, text="Welcome back", bg=CARD, fg=TEXT, font=F(20, "bold")).pack(anchor="w")
        tk.Label(box, text="Sign in to raise or track complaints", bg=CARD, fg=MUTED,
                 font=F(10)).pack(anchor="w", pady=(0, 22))

        field_label(box, "Username").pack(fill="x")
        user_e = entry(box)
        user_e.pack(fill="x", ipady=7, pady=(4, 14))
        user_e.insert(0, prefill)
        field_label(box, "Password").pack(fill="x")
        pass_e = entry(box, show="•")
        pass_e.pack(fill="x", ipady=7, pady=(4, 22))

        def do_login(event=None):
            row = db.login(user_e.get().strip(), pass_e.get())
            if row is None:
                messagebox.showerror("Sign in failed", "Wrong username or password.")
                return
            self.user = row
            self.show_main()

        button(box, "Sign In", do_login).pack(fill="x")
        self.bind("<Return>", do_login)

        link = tk.Label(box, text="New student?  Create an account", bg=CARD, fg=GREEN,
                        font=F(10, "bold"), cursor="hand2")
        link.pack(pady=(16, 0))
        link.bind("<Button-1>", lambda e: self.show_register())

        # one-click demo logins, handy during a demo
        tk.Frame(box, bg=BORDER, height=1).pack(fill="x", pady=18)
        tk.Label(box, text="QUICK DEMO", bg=CARD, fg=MUTED, font=F(8, "bold")).pack()
        demo = tk.Frame(box, bg=CARD)
        demo.pack(pady=(8, 0))

        def fill(u, p):
            user_e.delete(0, "end"); user_e.insert(0, u)
            pass_e.delete(0, "end"); pass_e.insert(0, p)

        button(demo, "Student", lambda: fill("student1", "student123"), primary=False).pack(side="left", padx=4)
        button(demo, "Admin", lambda: fill("admin", "admin123"), primary=False).pack(side="left", padx=4)
        user_e.focus_set()

    def show_register(self):
        self.clear()
        self.unbind("<Return>")
        self.brand_panel()

        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        box = card(right, padx=36, pady=30)
        box.place(relx=0.5, rely=0.5, anchor="center", width=560)

        tk.Label(box, text="Create student account", bg=CARD, fg=TEXT, font=F(18, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w")
        tk.Label(box, text="Use your official SRMIST details", bg=CARD, fg=MUTED, font=F(10)).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 16))

        labels = [("Full name", None), ("Username", None), ("Registration no. (RA...)", None),
                  ("SRMIST email", None), ("Department", None), ("Year", None),
                  ("Password", "•"), ("Confirm password", "•")]
        fields = {}
        for i, (text, show) in enumerate(labels):
            r, c = 2 + (i // 2) * 2, i % 2
            field_label(box, text).grid(row=r, column=c, sticky="w", padx=(0 if c == 0 else 12, 0))
            e = entry(box, show=show)
            e.grid(row=r + 1, column=c, sticky="ew", ipady=6, pady=(4, 12), padx=(0 if c == 0 else 12, 0))
            fields[text] = e
        box.columnconfigure(0, weight=1)
        box.columnconfigure(1, weight=1)

        def do_register():
            v = {k: e.get().strip() for k, e in fields.items()}
            if not all(v.values()):
                return messagebox.showwarning("Missing details", "Please fill in every field.")
            if not (v["Registration no. (RA...)"].upper().startswith("RA") and len(v["Registration no. (RA...)"]) >= 10):
                return messagebox.showwarning("Invalid", "Registration number should look like RA2511003010001.")
            if not v["SRMIST email"].lower().endswith("@srmist.edu.in"):
                return messagebox.showwarning("Invalid", "Please use your @srmist.edu.in email.")
            if len(v["Password"]) < 6:
                return messagebox.showwarning("Weak password", "Password must be at least 6 characters.")
            if v["Password"] != v["Confirm password"]:
                return messagebox.showwarning("Mismatch", "Passwords do not match.")

            ok, msg = db.register_student(
                v["Username"], v["Password"], v["Full name"], v["Registration no. (RA...)"].upper(),
                v["SRMIST email"].lower(), f'{v["Department"]} · {v["Year"]}')
            if ok:
                messagebox.showinfo("Welcome!", msg)
                self.show_login(prefill=v["Username"])
            else:
                messagebox.showerror("Could not register", msg)

        btns = tk.Frame(box, bg=CARD)
        btns.grid(row=20, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        button(btns, "Create Account", do_register).pack(side="right")
        button(btns, "Back to Sign In", self.show_login, primary=False).pack(side="right", padx=8)

    # ============================================================== main layout (after login)

    def show_main(self):
        self.clear()
        self.unbind("<Return>")
        is_admin = self.user["role"] == "admin"

        # ---- sidebar
        side = tk.Frame(self, bg=DARK, width=240)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        tk.Label(side, image=self.logo_small, bg=DARK).pack(anchor="w", padx=16, pady=(20, 18))

        # user badge with initials
        badge = tk.Frame(side, bg="#1F4D39", padx=12, pady=10)
        badge.pack(fill="x", padx=16, pady=(0, 20))
        initials = "".join(p[0] for p in self.user["name"].split()[:2]).upper()
        av = tk.Canvas(badge, width=38, height=38, bg="#1F4D39", highlightthickness=0)
        av.create_oval(1, 1, 37, 37, fill=GREEN, outline="")
        av.create_text(19, 19, text=initials, fill="white", font=F(10, "bold"))
        av.pack(side="left")
        info = tk.Frame(badge, bg="#1F4D39")
        info.pack(side="left", padx=10)
        tk.Label(info, text=self.user["name"], bg="#1F4D39", fg="white", font=F(10, "bold")).pack(anchor="w")
        tk.Label(info, text="Administrator" if is_admin else self.user["reg_no"], bg="#1F4D39",
                 fg=SOFT, font=F(8)).pack(anchor="w")

        tk.Label(side, text="MENU", bg=DARK, fg="#6E8F7E", font=F(8, "bold")).pack(anchor="w", padx=22)
        if is_admin:
            pages = [("Dashboard", self.page_dashboard), ("All Complaints", self.page_complaints)]
        else:
            pages = [("Dashboard", self.page_dashboard), ("New Complaint", self.page_new_complaint),
                     ("My Complaints", self.page_complaints), ("Help & FAQ", self.page_help)]

        self.nav = {}
        for name, func in pages:
            b = tk.Label(side, text="   " + name, bg=DARK, fg=SOFT, font=F(10), anchor="w",
                         cursor="hand2", padx=12, pady=10)
            b.pack(fill="x", padx=12, pady=2)
            b.bind("<Button-1>", lambda e, n=name: self.go(n))
            b.bind("<Enter>", lambda e, w=b, n=name: w.config(bg="#1F4D39") if n != self.active else None)
            b.bind("<Leave>", lambda e, w=b, n=name: w.config(bg=DARK) if n != self.active else None)
            self.nav[name] = (b, func)

        out = tk.Label(side, text="   Sign out", bg=DARK, fg="#E8A6A4", font=F(10), anchor="w",
                       cursor="hand2", padx=12, pady=10)
        out.pack(side="bottom", fill="x", padx=12, pady=18)
        out.bind("<Button-1>", lambda e: messagebox.askyesno("Sign out", "Sign out of UniResolve?") and self.show_login())

        # ---- content area (pages are drawn in here)
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        self.active = None
        self.go("Dashboard")

    def go(self, name):
        """Highlight the menu item and draw that page."""
        self.active = name
        for n, (b, _) in self.nav.items():
            b.config(bg=GREEN if n == name else DARK, fg="white" if n == name else SOFT,
                     font=F(10, "bold" if n == name else "normal"))
        for w in self.content.winfo_children():
            w.destroy()
        self.nav[name][1]()

    def page_header(self, title, subtitle, action=None):
        head = tk.Frame(self.content, bg=BG)
        head.pack(fill="x", padx=32, pady=(28, 18))
        left = tk.Frame(head, bg=BG)
        left.pack(side="left")
        tk.Label(left, text=title, bg=BG, fg=TEXT, font=F(20, "bold")).pack(anchor="w")
        tk.Label(left, text=subtitle, bg=BG, fg=MUTED, font=F(10)).pack(anchor="w")
        if action:
            button(head, action[0], action[1]).pack(side="right")

    # ============================================================== pages

    def page_dashboard(self):
        is_admin = self.user["role"] == "admin"
        hour = datetime.now().hour
        greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
        first = self.user["name"].split()[0]

        if is_admin:
            self.page_header(f"{greet}, {first}", "Overview of every complaint on campus",
                             ("View All Complaints", lambda: self.go("All Complaints")))
        else:
            self.page_header(f"{greet}, {first}", "Here is what is happening with your complaints",
                             ("+  New Complaint", lambda: self.go("New Complaint")))

        uid = None if is_admin else self.user["id"]
        stats = db.get_stats(uid)

        # ---- four stat cards
        row = tk.Frame(self.content, bg=BG)
        row.pack(fill="x", padx=32)
        for i, (label, color) in enumerate([("Total", TEXT), ("Pending", STATUS_COLORS["Pending"]),
                                            ("In Progress", STATUS_COLORS["In Progress"]),
                                            ("Resolved", STATUS_COLORS["Resolved"])]):
            c = card(row)
            c.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 14, 0))
            row.columnconfigure(i, weight=1)
            tk.Frame(c, bg=color, width=5).pack(side="left", fill="y")
            body = tk.Frame(c, bg=CARD, padx=18, pady=16)
            body.pack(side="left", fill="both")
            tk.Label(body, text=label.upper(), bg=CARD, fg=MUTED, font=F(8, "bold")).pack(anchor="w")
            tk.Label(body, text=str(stats[label]), bg=CARD, fg=color, font=F(26, "bold")).pack(anchor="w")

        # ---- bottom: recent complaints (+ category chart for admin)
        bottom = tk.Frame(self.content, bg=BG)
        bottom.pack(fill="both", expand=True, padx=32, pady=22)

        recent = card(bottom)
        recent.pack(side="left", fill="both", expand=True)
        tk.Label(recent, text="Recent complaints", bg=CARD, fg=TEXT, font=F(12, "bold")).pack(
            anchor="w", padx=18, pady=(14, 8))
        self.complaints_table(recent, db.get_complaints(uid)[:8], compact=is_admin)

        if is_admin:
            chart = card(bottom, padx=18, pady=14, width=300)
            chart.pack(side="left", fill="y", padx=(14, 0))
            chart.pack_propagate(False)
            tk.Label(chart, text="By category", bg=CARD, fg=TEXT, font=F(12, "bold")).pack(anchor="w", pady=(0, 10))
            counts = db.get_category_counts()
            top = max([n for _, n in counts], default=1)
            for cat, n in counts:
                line = tk.Frame(chart, bg=CARD)
                line.pack(fill="x", pady=6)
                tk.Label(line, text=cat, bg=CARD, fg=TEXT, font=F(9)).pack(side="left")
                tk.Label(line, text=str(n), bg=CARD, fg=MUTED, font=F(9, "bold")).pack(side="right")
                track = tk.Frame(chart, bg=LIGHT, height=8)
                track.pack(fill="x")
                tk.Frame(track, bg=GREEN, height=8).place(relwidth=n / top, relheight=1)

    def page_new_complaint(self):
        self.page_header("Raise a new complaint", "Describe the problem and we will route it to the right team")

        form = card(self.content, padx=28, pady=24)
        form.pack(fill="x", padx=32)
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(2, weight=1)

        field_label(form, "Title").grid(row=0, column=0, columnspan=3, sticky="w")
        title_e = entry(form)
        title_e.grid(row=1, column=0, columnspan=3, sticky="ew", ipady=7, pady=(4, 14))

        field_label(form, "Category").grid(row=2, column=0, sticky="w")
        field_label(form, "Location (pick or type your own)").grid(row=2, column=1, sticky="w", padx=12)
        field_label(form, "Priority").grid(row=2, column=2, sticky="w")
        cat_c = combo(form, db.CATEGORIES)
        loc_c = combo(form, db.LOCATIONS, editable=True)
        pri_c = combo(form, db.PRIORITIES)
        pri_c.set("Medium")
        cat_c.grid(row=3, column=0, sticky="ew", pady=(4, 14))
        loc_c.grid(row=3, column=1, sticky="ew", pady=(4, 14), padx=12)
        pri_c.grid(row=3, column=2, sticky="ew", pady=(4, 14))

        field_label(form, "Description").grid(row=4, column=0, columnspan=3, sticky="w")
        desc = tk.Text(form, height=7, font=F(10), relief="flat", bg=FIELD, fg=TEXT, wrap="word",
                       highlightthickness=1, highlightbackground=BORDER, highlightcolor=GREEN, padx=8, pady=6)
        desc.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(4, 18))

        def clear_form():
            title_e.delete(0, "end")
            desc.delete("1.0", "end")
            cat_c.set(db.CATEGORIES[0]); loc_c.set(db.LOCATIONS[0]); pri_c.set("Medium")

        def submit():
            title, text, loc = title_e.get().strip(), desc.get("1.0", "end").strip(), loc_c.get().strip()
            if not title or not text or not loc:
                return messagebox.showwarning("Missing details", "Please add a title, location and description.")
            new_id = db.add_complaint(self.user["id"], title, cat_c.get(), loc, pri_c.get(), text)
            messagebox.showinfo("Complaint submitted",
                                f"Your ticket number is {db.ticket_id(new_id)}.\nYou can track it under My Complaints.")
            self.go("My Complaints")

        btns = tk.Frame(form, bg=CARD)
        btns.grid(row=6, column=0, columnspan=3, sticky="e")
        button(btns, "Clear", clear_form, primary=False).pack(side="left", padx=8)
        button(btns, "Submit Complaint", submit).pack(side="left")

        tip = tk.Label(self.content, bg=BG, fg=MUTED, font=F(9), justify="left",
                       text="Tip: be specific about the room or block number so the maintenance team can find it quickly.")
        tip.pack(anchor="w", padx=34, pady=12)

    def page_complaints(self):
        is_admin = self.user["role"] == "admin"
        if is_admin:
            self.page_header("All complaints", "Double-click any complaint to update its status")
        else:
            self.page_header("My complaints", "Double-click any complaint to see full details",
                             ("+  New Complaint", lambda: self.go("New Complaint")))

        # ---- search + filter bar
        bar = card(self.content, padx=16, pady=12)
        bar.pack(fill="x", padx=32)
        tk.Label(bar, text="Search", bg=CARD, fg=MUTED, font=F(9, "bold")).pack(side="left")
        search_e = entry(bar)
        search_e.pack(side="left", ipady=5, padx=(8, 20), fill="x", expand=True)
        tk.Label(bar, text="Status", bg=CARD, fg=MUTED, font=F(9, "bold")).pack(side="left")
        status_c = combo(bar, ["All"] + db.STATUSES)
        status_c.config(width=14)
        status_c.pack(side="left", padx=(8, 0))

        holder = card(self.content)
        holder.pack(fill="both", expand=True, padx=32, pady=(14, 28))

        def refresh(event=None):
            for w in holder.winfo_children():
                w.destroy()
            rows = db.get_complaints(None if is_admin else self.user["id"],
                                     status_c.get(), search_e.get().strip())
            self.complaints_table(holder, rows)

        search_e.bind("<KeyRelease>", refresh)
        status_c.bind("<<ComboboxSelected>>", refresh)
        refresh()

    def page_help(self):
        self.page_header("Help & FAQ", "Answers to common questions and how to reach the helpdesk")

        body = tk.Frame(self.content, bg=BG)
        body.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        # ---- left: frequently asked questions
        faq = card(body, padx=24, pady=18)
        faq.pack(side="left", fill="both", expand=True)
        tk.Label(faq, text="Frequently asked questions", bg=CARD, fg=TEXT, font=F(12, "bold")).pack(anchor="w", pady=(0, 6))
        questions = [
            ("How do I raise a complaint?",
             "Open New Complaint from the menu. Add a title, pick the category, location and priority, "
             "describe the problem and press Submit. You will get a ticket number like CMP009."),
            ("How do I track my complaint?",
             "Open My Complaints. Use the search box or the status filter, and double-click a complaint "
             "to see its full details and the admin's remarks."),
            ("What do the statuses mean?",
             "Pending: received and waiting for review.\n"
             "In Progress: someone is working on it.\n"
             "Resolved: the problem has been fixed."),
            ("Who resolves my complaint?",
             "The campus facility administrators. They review every complaint, update its status and "
             "add remarks about what was done."),
            ("My complaint is still Pending. What should I do?",
             "If a High priority complaint stays Pending for more than 48 hours, visit or email the "
             "helpdesk with your ticket number."),
            ("Can I edit or delete a complaint?",
             "Students cannot change a complaint after submitting it. If something is wrong, contact the "
             "helpdesk with your ticket number."),
        ]
        for i, (q, a) in enumerate(questions):
            if i:
                tk.Frame(faq, bg=BORDER, height=1).pack(fill="x", pady=8)
            tk.Label(faq, text=q, bg=CARD, fg=TEXT, font=F(10, "bold"), anchor="w").pack(fill="x")
            tk.Label(faq, text=a, bg=CARD, fg=TEXT, font=F(10), wraplength=560, justify="left",
                     anchor="w").pack(fill="x", pady=(2, 0))

        # ---- right: contact details
        contact = card(body, padx=22, pady=18, width=310)
        contact.pack(side="left", fill="y", padx=(14, 0))
        contact.pack_propagate(False)
        tk.Label(contact, text="Contact the helpdesk", bg=CARD, fg=TEXT, font=F(12, "bold")).pack(anchor="w", pady=(0, 12))
        for title, text in [("Office", "Room 104, Ground Floor\nUniversity Building, SRMIST"),
                            ("Hours", "Mon – Fri: 9:00 AM – 5:00 PM\nSat: 9:00 AM – 1:00 PM"),
                            ("Email", "helpdesk@srmist.edu.in")]:
            tk.Frame(contact, bg=GREEN, height=2, width=28).pack(anchor="w")
            tk.Label(contact, text=title.upper(), bg=CARD, fg=MUTED, font=F(8, "bold")).pack(anchor="w", pady=(6, 2))
            tk.Label(contact, text=text, bg=CARD, fg=TEXT, font=F(10), justify="left").pack(anchor="w", pady=(0, 16))

    # ============================================================== table + details popup

    def complaints_table(self, parent, rows, compact=False):
        is_admin = self.user["role"] == "admin"
        if not rows:
            tk.Label(parent, text="No complaints to show yet.", bg=CARD, fg=MUTED, font=F(10)).pack(pady=40)
            return

        if compact:
            cols = ["Title", "Status", "Date"]
        else:
            cols = ["Title"] + (["Student"] if is_admin else []) + ["Category", "Location", "Priority", "Status", "Date"]
        widths = {"Title": 150, "Student": 120, "Category": 125, "Location": 135,
                  "Priority": 80, "Status": 100, "Date": 100}

        frame = tk.Frame(parent, bg=CARD)
        frame.pack(fill="both", expand=True, padx=1, pady=(0, 1))
        # column "#0" holds the coloured dot + ticket number, the rest are normal columns
        tree = ttk.Treeview(frame, columns=cols, show="tree headings", selectmode="browse")
        tree.heading("#0", text="TICKET", anchor="w")
        tree.column("#0", width=105, stretch=False, anchor="w")
        for c in cols:
            tree.heading(c, text=c.upper(), anchor="w")
            tree.column(c, width=widths[c], minwidth=60, anchor="w", stretch=(c == "Title"))
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        tree.tag_configure("stripe", background="#FAFCFB")

        by_id = {}
        for i, r in enumerate(rows):
            data = {"Title": r["title"], "Student": r["student_name"], "Category": r["category"],
                    "Location": r["location"], "Priority": r["priority"], "Status": r["status"],
                    "Date": nice_date(r["created_at"])}
            tags = ["stripe"] if i % 2 else []
            item = tree.insert("", "end", text=" " + db.ticket_id(r["id"]), image=self.dots[r["status"]],
                               values=[data[c] for c in cols], tags=tags)
            by_id[item] = r

        tree.bind("<Double-1>", lambda e: tree.focus() and self.show_details(by_id[tree.focus()]))

    def show_details(self, c):
        """Popup with full complaint details. Admin also gets status + remarks editing."""
        is_admin = self.user["role"] == "admin"
        win = tk.Toplevel(self, bg=CARD)
        win.title(f"Complaint {db.ticket_id(c['id'])}")
        win.geometry(f"580x{580 if is_admin else 480}")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        pad = tk.Frame(win, bg=CARD, padx=28, pady=22)
        pad.pack(fill="both", expand=True)

        top = tk.Frame(pad, bg=CARD)
        top.pack(fill="x")
        tk.Label(top, text=db.ticket_id(c["id"]), bg=CARD, fg=MUTED, font=F(9, "bold")).pack(side="left")
        color = STATUS_COLORS[c["status"]]
        tk.Label(top, text=f"  {c['status']}  ", bg=color, fg="white", font=F(9, "bold")).pack(side="right")
        tk.Label(pad, text=c["title"], bg=CARD, fg=TEXT, font=F(15, "bold"), wraplength=520,
                 justify="left").pack(anchor="w", pady=(6, 14))

        grid = tk.Frame(pad, bg=FIELD, padx=14, pady=10)
        grid.pack(fill="x")
        facts = [("Category", c["category"]), ("Location", c["location"]),
                 ("Priority", c["priority"]), ("Raised by", f'{c["student_name"]} ({c["reg_no"]})'),
                 ("Created", c["created_at"][:16]), ("Last updated", c["updated_at"][:16])]
        for i, (k, v) in enumerate(facts):
            tk.Label(grid, text=k, bg=FIELD, fg=MUTED, font=F(9)).grid(row=i // 2 * 2, column=i % 2, sticky="w", padx=(0, 30))
            fg = PRIORITY_COLORS.get(v, TEXT) if k == "Priority" else TEXT
            tk.Label(grid, text=v, bg=FIELD, fg=fg, font=F(10, "bold")).grid(row=i // 2 * 2 + 1, column=i % 2, sticky="w", padx=(0, 30), pady=(0, 8))

        tk.Label(pad, text="Description", bg=CARD, fg=TEXT, font=F(10, "bold")).pack(anchor="w", pady=(16, 4))
        tk.Label(pad, text=c["description"], bg=CARD, fg=TEXT, font=F(10), wraplength=520,
                 justify="left").pack(anchor="w")

        tk.Label(pad, text="Admin remarks", bg=CARD, fg=TEXT, font=F(10, "bold")).pack(anchor="w", pady=(16, 4))
        if not is_admin:
            tk.Label(pad, text=c["remarks"] or "No remarks yet. The team will update this soon.", bg=CARD,
                     fg=TEXT if c["remarks"] else MUTED, font=F(10), wraplength=520, justify="left").pack(anchor="w")
            button(pad, "Close", win.destroy, primary=False).pack(side="bottom", anchor="e")
            return

        remarks = tk.Text(pad, height=4, font=F(10), relief="flat", bg=FIELD, fg=TEXT, wrap="word",
                          highlightthickness=1, highlightbackground=BORDER, highlightcolor=GREEN, padx=8, pady=6)
        remarks.insert("1.0", c["remarks"] or "")
        remarks.pack(fill="x")

        actions = tk.Frame(pad, bg=CARD)
        actions.pack(side="bottom", fill="x")
        tk.Label(actions, text="Status", bg=CARD, fg=MUTED, font=F(9, "bold")).pack(side="left")
        status_c = combo(actions, db.STATUSES)
        status_c.set(c["status"])
        status_c.config(width=13)
        status_c.pack(side="left", padx=8)

        def save():
            db.update_status(c["id"], status_c.get(), remarks.get("1.0", "end").strip())
            win.destroy()
            messagebox.showinfo("Saved", f"{db.ticket_id(c['id'])} is now '{status_c.get()}'.")
            self.go(self.active)          # redraw the page so the table shows the change

        def delete():
            if not messagebox.askyesno("Delete complaint",
                                       f"Permanently delete {db.ticket_id(c['id'])}?\nThis cannot be undone.",
                                       icon="warning", parent=win):
                return
            db.delete_complaint(c["id"])
            win.destroy()
            messagebox.showinfo("Deleted", f"{db.ticket_id(c['id'])} has been deleted.")
            self.go(self.active)

        button(actions, "Save Changes", save).pack(side="right")
        button(actions, "Cancel", win.destroy, primary=False).pack(side="right", padx=8)
        # only resolved complaints can be deleted, so open issues are never lost by mistake
        if c["status"] == "Resolved":
            button(actions, "Delete", delete, primary=False, danger=True).pack(side="right")


if __name__ == "__main__":
    UniResolveApp().mainloop()
