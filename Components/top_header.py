from tkinter import *

class Header(Frame):
    def __init__(self, App):
        t = App.theme                                   # colors from main.py
        super().__init__(App.root, bg=t["surface"])

        self.App = App

        heading = Label(self, text="Photo Editing Application", font=self.App.adjust_font(14, bold=True),
                        bg=t["surface"], fg=t["accent"], anchor="w")
        self.App.place_component(heading, 30, 5, 1000, 35)

        minimize_button = Button(self, text="—", font=self.App.adjust_font(12, bold=True),
                                 bg=t["surface"], fg=t["text"], activebackground=t["accent_light"], activeforeground=t["accent"],
                                 relief=FLAT, bd=0, highlightthickness=0, cursor="hand2", command=self.Minimize)
        self.App.place_component(minimize_button, 1536-90, 5, 40, 35)

        close_button = Button(self, text="✕", font=self.App.adjust_font(12, bold=True),
                              bg=t["surface"], fg=t["text"], activebackground=t["danger"], activeforeground="#ffffff",
                              relief=FLAT, bd=0, highlightthickness=0, cursor="hand2", command=self.Exit)
        self.App.place_component(close_button, 1536-45, 5, 40, 35)

        # hover colors (light blue for minimize, red for close)
        for button, hover_bg, hover_fg in [(minimize_button, t["accent_light"], t["accent"]),
                                           (close_button, t["danger"], "#ffffff")]:
            button.bind("<Enter>", lambda e, b=button, bg=hover_bg, fg=hover_fg: b.config(bg=bg, fg=fg))
            button.bind("<Leave>", lambda e, b=button: b.config(bg=t["surface"], fg=t["text"]))

        # thin line under the header
        Frame(self, bg=t["border"]).place(x=0, rely=1, relwidth=1, height=1, anchor="sw")

    def Exit(self):
        self.App.root.destroy()
        exit()

    def Minimize(self):
        self.App.root.iconify()