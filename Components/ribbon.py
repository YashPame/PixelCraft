from tkinter import *
from tkinter import ttk
from Components.ribbon_home import RibbonHome
from Components.ribbon_help import RibbonHelp

class Ribbon(Frame):
    def __init__(self, App):
        super().__init__(App.root)

        self.App = App

        style = ttk.Style()
        style.configure("Ribbon.TNotebook.Tab", padding=(self.App.scale_x(6), self.App.scale_y(4)), font=self.App.adjust_font(12, bold=True))



        self.Notebook = ttk.Notebook(self, style="Ribbon.TNotebook")

        self.App.place_component(self.Notebook, 0, 0, 1520, 150)

        self.HomeTab = RibbonHome(self.App, self.Notebook)
        self.HelpTab = RibbonHelp(self.App, self.Notebook)

        self.Notebook.add(self.HomeTab, text="Home")
        self.Notebook.add(self.HelpTab, text="Help")