from tkinter import *

class Header(Frame):
    def __init__(self, App):
        super().__init__(App.root)

        self.App = App

        heading = Label(self, text="Photo Editing Application", font=self.App.adjust_font(14, bold=True), bd=3, relief=RIDGE)
        self.App.place_component(heading, 5, 5, 1430, 35)

        minimize_button = Button(self, text="-", font=self.App.adjust_font(12, bold=True), relief=RIDGE, bd=3, command=self.Minimize)
        self.App.place_component(minimize_button, 1440, 5, 35, 35)
        
        close_button = Button(self, text="X", font=self.App.adjust_font(12, bold=True), relief=RIDGE, bd=3, command=self.Exit)
        self.App.place_component(close_button, 1480, 5, 35, 35)
    
    def Exit(self):
        self.App.root.destroy()
        exit()

    def Minimize(self):
        self.App.root.iconify()