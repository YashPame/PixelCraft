from tkinter import *
from tkinter import ttk

class RibbonHelp(Frame):
    def __init__(self, App, Parent):
        super().__init__(Parent)

        self.App = App

        heading = Label(self, text="RibbonHelp", font=self.App.adjust_font(12, bold=True), bd=3, relief=RIDGE)
        self.App.place_component(heading, 5, 5, 200, 35)