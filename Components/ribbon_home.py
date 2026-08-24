from tkinter import *
from tkinter import ttk

from tkinter import filedialog


class RibbonHome(Frame):
    def __init__(self, App, Parent):
        super().__init__(Parent)

        self.App = App
        self.Editor = self.App.editor

        # heading = Label(self, text="Home", font=self.App.adjust_font(12, bold=True), bd=3, relief=RIDGE)
        # self.App.place_component(heading, 5, 5, 200, 35)

        open_img_button = Button(self, text="Open Image", font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1, command=self.Editor.OpenImage)
        self.App.place_component(open_img_button, 5, 5, 100, 35)

        save_img_button = Button(self, text="Save Image", font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)
        self.App.place_component(save_img_button, 5, 45, 100, 35)

        