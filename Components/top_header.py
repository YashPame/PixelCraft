from tkinter import *
from Components.base_component import BaseComponent
from utils import *

class Header(BaseComponent):
    def __init__(self, App):
        super().__init__(App)

        self.config(bg="red")

        heading = Label(self, text="Photo Editing Application", font=self.adjust_font(12, bold=True), bd=3, relief=RIDGE)
        self.place_component(heading, 5, 5, 1400, 50)

        minimize_button = Button(self, text="-", font=self.adjust_font(12, bold=True), relief=RIDGE, bd=3, command=self.Minimize)
        self.place_component(minimize_button, 1410, 5, 50, 50)
        
        close_button = Button(self, text="X", font=self.adjust_font(12, bold=True), relief=RIDGE, bd=3, command=self.Exit)
        self.place_component(close_button, 1465, 5, 50, 50)
    
    def Exit(self):
        self.App.root.destroy()
        exit()

    def Minimize(self):
        self.App.root.iconify()