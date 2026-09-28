from tkinter import *
from tkinter import ttk
from Components.action_bar import ActionBar
from Components.ribbon_help import RibbonHelp

class Ribbon(Frame):
    def __init__(self, App):
        super().__init__(App.root)

        self.App = App

        self.HomeTab = ActionBar(self.App)
        self.App.place_component(self.HomeTab, 0, 0, 1520, 145)