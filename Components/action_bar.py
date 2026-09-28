from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import filedialog


class ActionBar(Frame):
    def __init__(self, App):
        super().__init__(App.root)


        self.App = App
        self.Editor = self.App.editor

        self.CreateButtons()
        self.App.hasImage.trace_add("write", self.UpdateButtons)

    def CreateButtons(self):
        self.CoreTitleButtons = Frame(self)
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


            left_options_frame = Frame(self.CoreTitleButtons, bd=1, relief=SOLID)
            self.App.place_component(left_options_frame, 50, 15, 345, 50)

            zoom_in_button = Button(left_options_frame, image=self.App.IconImage_ZoomIn, font=self.App.adjust_font(20, bold=True), relief=RAISED, bd=1)
            zoom_out_button = Button(left_options_frame, image=self.App.IconImage_ZoomOut, font=self.App.adjust_font(20, bold=True), relief=RAISED, bd=1)
            zoom_percentage_label = Label(left_options_frame, text="100%", font=self.App.adjust_font(12, bold=True), bg="SYSTEMBUTTONFACE")

            seperator1 = Frame(left_options_frame, bg="black")

            reset_button = Button(left_options_frame, text="Reset", font=self.App.adjust_font(12, bold=True), relief=RAISED, bd=1)
            undo_button = Button(left_options_frame, image=self.App.IconImage_Undo, font=self.App.adjust_font(12, bold=True), relief=RAISED, bd=1)
            redo_button = Button(left_options_frame, image=self.App.IconImage_Redo, font=self.App.adjust_font(12, bold=True), relief=RAISED, bd=1)

            self.App.place_component(zoom_in_button, 10, 10, 30, 30)
            self.App.place_component(zoom_out_button, 50, 10, 30, 30)
            self.App.place_component(zoom_percentage_label, 90, 10, 50, 30)  
            self.App.place_component(seperator1, 150, 10, 2, 30)
            self.App.place_component(reset_button, 160, 10, 50, 30)
            self.App.place_component(undo_button, 220, 10, 50, 30)
            self.App.place_component(redo_button, 280, 10, 50, 30)
            


            right_options_frame = Frame(self.CoreTitleButtons)
            self.App.place_component(right_options_frame, 1520-250, 15, 200, 50)

            save_button = Button(right_options_frame, text="Save", font=self.App.adjust_font(12, bold=True), relief=RAISED, bd=1)
            cancel_button = Button(right_options_frame, text="Cancel", font=self.App.adjust_font(12, bold=True), relief=RAISED, bd=1)

            self.App.place_component(save_button, 10, 5, 100, 40)
            self.App.place_component(cancel_button, 120, 5, 70, 40)


    def UpdateButtons(self, *args):
        self.CoreTitleButtons.destroy()
        self.CreateButtons()