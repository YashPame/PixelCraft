from tkinter import *
from tkinter import font

APP_NAME = "PixelCraft"
VERSION = "1.0"
DEVELOPERS = ["Yash Pame", "Ansh Choube"]

class Header(Frame):
    def __init__(self, App):
        t = App.theme                                   # colors from main.py
        super().__init__(App.root, bg=t["surface"])

        self.App = App

        logo_font = "Segoe Script" if "Segoe Script" in font.families() else t["font"]
        # fills the row, from the left edge up to the info button
        heading = Label(self, text=APP_NAME, font=self.App.adjust_font(20, font_name=logo_font, bold=True),
                        bg=t["surface"], fg=t["accent"], anchor="w")
        self.App.place_component(heading, 30, 0, 1536 - 130 - 40, 45)

        info_button = Button(self, text="ℹ", font=self.App.adjust_font(12, bold=True),
                             bg=t["surface"], fg=t["text"], activebackground=t["accent_light"], activeforeground=t["accent"],
                             relief=FLAT, bd=0, highlightthickness=0, cursor="hand2", command=self.ShowInfo)
        self.App.place_component(info_button, 1536-90-40, 5, 40, 35)

        minimize_button = Button(self, text="—", font=self.App.adjust_font(12, bold=True),
                                 bg=t["surface"], fg=t["text"], activebackground=t["accent_light"], activeforeground=t["accent"],
                                 relief=FLAT, bd=0, highlightthickness=0, cursor="hand2", command=self.Minimize)
        self.App.place_component(minimize_button, 1536-90, 5, 40, 35)

        close_button = Button(self, text="✕", font=self.App.adjust_font(12, bold=True),
                              bg=t["surface"], fg=t["text"], activebackground=t["danger"], activeforeground="#ffffff",
                              relief=FLAT, bd=0, highlightthickness=0, cursor="hand2", command=self.Exit)
        self.App.place_component(close_button, 1536-45, 5, 40, 35)

        # hover colors (light blue for info / minimize, red for close)
        for button, hover_bg, hover_fg in [(info_button, t["accent_light"], t["accent"]),
                                           (minimize_button, t["accent_light"], t["accent"]),
                                           (close_button, t["danger"], "#ffffff")]:
            button.bind("<Enter>", lambda e, b=button, bg=hover_bg, fg=hover_fg: b.config(bg=bg, fg=fg))
            button.bind("<Leave>", lambda e, b=button: b.config(bg=t["surface"], fg=t["text"]))

        # thin line under the header
        Frame(self, bg=t["border"]).place(x=0, rely=1, relwidth=1, height=1, anchor="sw")

        self.info_window = None

    def Exit(self):
        self.App.root.destroy()
        exit()

    def Minimize(self):
        self.App.root.iconify()

    # ---------------- Info window ----------------

    def ShowInfo(self):
        # only one info window at a time
        if self.info_window is not None and self.info_window.winfo_exists():
            self.info_window.lift()
            return

        t = self.App.theme
        f = self.App.adjust_font
        win = self.info_window = Toplevel(self.App.root, bg=t["sidebar"])
        win.title(f"About {APP_NAME}")
        win.resizable(False, False)
        win.transient(self.App.root)
        win.attributes("-topmost", True)       # stay above the fullscreen app
        win.grab_set()
        win.bind("<Escape>", lambda e: win.destroy())

        body = Frame(win, bg=t["sidebar"])
        body.pack(padx=28, pady=(22, 20))

        # ----- name, version, description -----
        logo_font = "Segoe Script" if "Segoe Script" in font.families() else t["font"]
        top = Frame(body, bg=t["sidebar"])
        top.pack(fill=X)
        Label(top, text=APP_NAME, font=f(22, font_name=logo_font, bold=True), bg=t["sidebar"], fg=t["accent"]).pack(side=LEFT)
        Label(top, text=f"v{VERSION}", font=f(9, bold=True), bg=t["accent_light"], fg=t["accent"],
              padx=8, pady=2).pack(side=LEFT, padx=12, pady=(10, 0))

        Label(body, text="A simple, fast photo editor for everyday edits: fix light and color, crop, "
                         "add filters, draw, remove objects and backgrounds, then save in the format you need.",
              font=f(10), bg=t["sidebar"], fg=t["muted"], wraplength=self.App.scale_x(560),
              justify=LEFT).pack(anchor="w", pady=(4, 0))

        # ----- developers -----
        self.InfoSection(body, "Developed by")
        devs = Frame(body, bg=t["sidebar"])
        devs.pack(anchor="w", pady=(8, 0))
        for name in DEVELOPERS:
            card = Frame(devs, bg=t["surface"], highlightthickness=1, highlightbackground=t["border"])
            card.pack(side=LEFT, padx=(0, 12))
            # round avatar with initials
            size = self.App.scale_x(38)
            avatar = Canvas(card, width=size, height=size, bg=t["surface"], highlightthickness=0)
            avatar.pack(side=LEFT, padx=(10, 8), pady=8)
            avatar.create_oval(1, 1, size - 1, size - 1, fill=t["accent"], outline="")
            initials = "".join(part[0] for part in name.split()[:2]).upper()
            avatar.create_text(size / 2, size / 2, text=initials, fill="#ffffff", font=f(11, bold=True))
            Label(card, text=name, font=f(11, bold=True), bg=t["surface"], fg=t["text"]).pack(side=LEFT, padx=(0, 14))

        # center on the app
        win.update_idletasks()
        root = self.App.root
        x = root.winfo_x() + (root.winfo_width() - win.winfo_width()) // 2
        y = root.winfo_y() + (root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

    def InfoSection(self, parent, title):
        # thin line, then a small title (same look as the side panels)
        t = self.App.theme
        Frame(parent, bg=t["border"], height=1).pack(fill=X, pady=(16, 0))
        Label(parent, text=title, font=self.App.adjust_font(11, bold=True),
              bg=t["sidebar"], fg=t["text"]).pack(anchor="w", pady=(10, 0))