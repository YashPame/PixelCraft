from tkinter import *
from tkinter import ttk

from tkinter import filedialog


class RibbonHome(Frame):
    def __init__(self, App, Parent):
        super().__init__(Parent)

        self.config(relief=RIDGE, bd=3)

        self.App = App
        self.Editor = self.App.editor


        open_img_button = Button(self, text="Open Image", font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1, command=self.Editor.OpenImage)
        self.App.place_component(open_img_button, 10, 10, 100, 35)

        save_img_button = Button(self, text="Save Image", font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)
        self.App.place_component(save_img_button, 10, 55, 100, 35)

        self.App.place_component(Frame(self, width=2, bg="black"), 132, 5, 2, 90)


        undo_button = Button(self, text="Undo", font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)
        self.App.place_component(undo_button, 155, 10, 35, 35)

        redo_button = Button(self, text="Redo", font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)
        self.App.place_component(redo_button, 155, 55, 35, 35)

        self.App.place_component(Frame(self, width=2, bg="black"), 212, 5, 2, 90)

        copy_button = Button(self, text="Copy", font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)
        self.App.place_component(copy_button, 235, 10, 35, 35)

        cut_button = Button(self, text="Cut", font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)
        self.App.place_component(cut_button, 280, 10, 35, 35)

        paste_button = Button(self, text="Paste", font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)
        self.App.place_component(paste_button, 235, 55, 80, 35)

        self.App.place_component(Frame(self, width=2, bg="black"), 337, 5, 2, 90)
