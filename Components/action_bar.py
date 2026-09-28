from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import filedialog


class ActionBar(Frame):
    def __init__(self, App):
        super().__init__(App.root)

        self.config(bg="SYSTEMBUTTONFACE")

        self.App = App
        self.Editor = self.App.editor

        self.CreateButtons()
        self.App.hasImage.trace_add("write", self.UpdateButtons)

    def CreateButtons(self):
        self.CoreTitleButtons = Frame(self, bg="SYSTEMBUTTONFACE")
        self.CoreTitleButtons.place(x=0, y=0, width=1520, height=105)

        if self.App.hasImage.get() == False:
            open_img_button = Button(self.CoreTitleButtons, image=self.App.IconImage_OpenFile, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1, command=self.Editor.OpenImage)
            self.App.place_component(open_img_button, 1520/2-25, 15, 50, 50)

            open_img_label = Label(self.CoreTitleButtons, text="Open Image", font=self.App.adjust_font(12, bold=True), bg="SYSTEMBUTTONFACE")
            self.App.place_component(open_img_label, 1520/2-50, 65, 100, 50)

        else:
            crop_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Crop, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)
            brightness_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Brightenss, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)
            brush_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Brush, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)
            pencil_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Pencil, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)
            eraser_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Eraser, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)
            ai_features_button = Button(self.CoreTitleButtons, image=self.App.IconImage_AIFeatures, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1)

            self.App.place_component(crop_button, 1520/2-150, 15, 50, 50)
            self.App.place_component(brightness_button, 1520/2-90, 15, 50, 50)
            self.App.place_component(brush_button, 1520/2-30, 15, 50, 50)
            self.App.place_component(pencil_button, 1520/2+30, 15, 50, 50)
            self.App.place_component(eraser_button, 1520/2+90, 15, 50, 50)
            self.App.place_component(ai_features_button, 1520/2+150, 15, 50, 50)


        

    def UpdateButtons(self, *args):
        self.CoreTitleButtons.destroy()
        self.CreateButtons()