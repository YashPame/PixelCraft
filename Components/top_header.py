from tkinter import *
from tkinter import font

APP_NAME = "PixelCraft"
VERSION = "1.0"
DEVELOPERS = ["Yash Pame", "Ansh Choube"]

class Header(Frame):
    def __init__(self, App):
        t = App.theme
        super().__init__(App.root, bg=t["surface"])

        self.App = App
        self.logo_font = "Segoe Script" if "Segoe Script" in font.families() else t["font"]

        heading = Label(self, text=APP_NAME, font=self.App.adjust_font(20, font_name=self.logo_font, bold=True), bg=t["surface"], fg=t["accent"], anchor="w")
        self.App.place_component(heading, 30, 0, 1536 - 135 - 40, 45)

        self.MakeButton("ℹ", 1536-90-45, self.ShowInfo, t["accent_light"], t["accent"])
        self.MakeButton("—", 1536-90, self.Minimize, t["accent_light"], t["accent"])
        self.MakeButton("✕", 1536-45, self.Exit, t["danger"], "#ffffff")

        Frame(self, bg=t["border"]).place(x=0, rely=1, relwidth=1, height=1, anchor="sw")

        self.info_window = None

    def MakeButton(self, text, x, command, hover_bg, hover_fg):
        t = self.App.theme
        button = Button(self, text=text, font=self.App.adjust_font(12, bold=True),
                        bg=t["surface"], fg=t["text"], activebackground=hover_bg, activeforeground=hover_fg,
                        relief=FLAT, bd=0, highlightthickness=0, cursor="hand2", command=command)
        self.App.place_component(button, x, 5, 40, 35)

        button.bind("<Enter>", lambda e: button.config(bg=hover_bg, fg=hover_fg))
        button.bind("<Leave>", lambda e: button.config(bg=t["surface"], fg=t["text"]))

    def Exit(self):
        self.App.root.destroy()
        exit()

    def Minimize(self):
        self.App.root.iconify()


    def ShowInfo(self):
        if self.info_window is not None and self.info_window.winfo_exists():
            self.info_window.lift()
            return

        t = self.App.theme
        f = self.App.adjust_font
        win = self.info_window = Toplevel(self.App.root, bg=t["sidebar"])
        win.title(f"About {APP_NAME}")
        win.resizable(False, False)
        win.transient(self.App.root) # minimize and closes with main app
        win.attributes("-topmost", True)
        win.grab_set() # Cant click main app until it is closed
        win.bind("<Escape>", lambda e: win.destroy())

        body = Frame(win, bg=t["sidebar"])
        body.pack(padx=28, pady=(22, 20))

        top = Frame(body, bg=t["sidebar"])
        top.pack(fill=X)
        Label(top, text=APP_NAME, font=f(22, font_name=self.logo_font, bold=True), bg=t["sidebar"], fg=t["accent"]).pack(side=LEFT)
        Label(top, text=f"v{VERSION}", font=f(9, bold=True), bg=t["accent_light"], fg=t["accent"], padx=8, pady=2).pack(side=LEFT, padx=12, pady=(10, 0))

        Label(body, text="A simple, fast photo editor for everyday edits: fix light and color, crop, add filters, draw, remove objects and backgrounds, then save in the format you need.",
              font=f(10), bg=t["sidebar"], fg=t["muted"], wraplength=self.App.scale_x(560), justify=LEFT).pack(anchor="w", pady=(4, 0))

        Frame(body, bg=t["border"], height=1).pack(fill=X, pady=(16, 0))
        Label(body, text="Developed by", font=self.App.adjust_font(11, bold=True), bg=t["sidebar"], fg=t["text"]).pack(anchor="w", pady=(10, 0))
        
        devs = Frame(body, bg=t["sidebar"])
        devs.pack(anchor="w", pady=(8, 0))
        for name in DEVELOPERS:
            card = Frame(devs, bg=t["surface"], highlightthickness=1, highlightbackground=t["border"])
            card.pack(side=LEFT, padx=(0, 12))
            Label(card, text=name, font=f(11, bold=True), bg=t["surface"], fg=t["text"]).pack(padx=14, pady=8)

        # center on the app
        win.update_idletasks()
        root = self.App.root
        x = root.winfo_x() + (root.winfo_width() - win.winfo_width()) // 2
        y = root.winfo_y() + (root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")


        
        