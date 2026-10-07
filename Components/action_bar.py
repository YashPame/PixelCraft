from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from tkinter import filedialog
from Components.Panels.crop_panel import CropPanel
from Components.Panels.light_panel import LightPanel
from Components.Panels.drawing_panels import DrawingPanel
from Components.Panels.eraser_panel import EraserPanel
from Components.Panels.ai_panel import AIPanel
from Components.Panels.filters_panel import FiltersPanel
from Components.save_dialog import SaveDialog          # NEW

class ActionBar(Frame):
    def __init__(self, App):
        super().__init__(App.root)


        self.App = App
        self.Editor = self.App.editor
        self.PanelsFrame = None

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
            self.crop_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Crop, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1, command=lambda: self.TopButtonClicked("Crop"))
            self.brightness_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Brightenss, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1, command=lambda: self.TopButtonClicked("Brightness"))
            # brush icon opens the Filters panel
            self.filters_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Brush, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1, command=lambda: self.TopButtonClicked("Filters"))
            self.pencil_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Pencil, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1, command=lambda: self.TopButtonClicked("Pencil"))
            self.eraser_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Eraser, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1, command=lambda: self.TopButtonClicked("Eraser"))
            self.ai_features_button = Button(self.CoreTitleButtons, image=self.App.IconImage_AIFeatures, font=self.App.adjust_font(10, bold=True), relief=RAISED, bd=1, command=lambda: self.TopButtonClicked("AI Features"))
            
            self.App.place_component(self.crop_button, 1520/2-150, 15, 50, 50)
            self.App.place_component(self.brightness_button, 1520/2-90, 15, 50, 50)
            self.App.place_component(self.filters_button, 1520/2-30, 15, 50, 50)
            self.App.place_component(self.pencil_button, 1520/2+30, 15, 50, 50)
            self.App.place_component(self.eraser_button, 1520/2+90, 15, 50, 50)
            self.App.place_component(self.ai_features_button, 1520/2+150, 15, 50, 50)

            left_options_frame = Frame(self.CoreTitleButtons, bd=1, relief=SOLID)
            self.App.place_component(left_options_frame, 50, 15, 355, 50)

            zoom_in_button = Button(left_options_frame, image=self.App.IconImage_ZoomIn, font=self.App.adjust_font(20, bold=True), relief=RAISED, bd=1, command=self.Editor.ZoomIn)
            zoom_out_button = Button(left_options_frame, image=self.App.IconImage_ZoomOut, font=self.App.adjust_font(20, bold=True), relief=RAISED, bd=1, command=self.Editor.ZoomOut)
            zoom_percentage_label = Label(left_options_frame, textvariable=self.Editor.active_image.zoom_percentage, font=self.App.adjust_font(12, bold=True), bg="SYSTEMBUTTONFACE")
            seperator1 = Frame(left_options_frame, bg="black")

            reset_button = Button(left_options_frame, text="Reset", font=self.App.adjust_font(12, bold=True), relief=RAISED, bd=1, command=self.Editor.Reset)
            undo_button = Button(left_options_frame, image=self.App.IconImage_Undo, font=self.App.adjust_font(12, bold=True), relief=RAISED, bd=1, command=self.Editor.Undo)
            redo_button = Button(left_options_frame, image=self.App.IconImage_Redo, font=self.App.adjust_font(12, bold=True), relief=RAISED, bd=1, command=self.Editor.Redo)

            self.App.place_component(zoom_in_button, 10, 10, 30, 30)
            self.App.place_component(zoom_out_button, 50, 10, 30, 30)
            self.App.place_component(zoom_percentage_label, 90, 10, 60, 30)  
            self.App.place_component(seperator1, 160, 10, 2, 30)
            self.App.place_component(reset_button, 170, 10, 50, 30)
            self.App.place_component(undo_button, 230, 10, 50, 30)
            self.App.place_component(redo_button, 290, 10, 50, 30)
            
            right_options_frame = Frame(self.CoreTitleButtons)
            self.App.place_component(right_options_frame, 1520-250, 15, 200, 50)

            # CHANGED: Save and Cancel now do something
            save_button = Button(right_options_frame, text="Save", font=self.App.adjust_font(12, bold=True), relief=RAISED, bd=1, command=self.SaveClicked)
            cancel_button = Button(right_options_frame, text="Cancel", font=self.App.adjust_font(12, bold=True), relief=RAISED, bd=1, command=self.CancelClicked)

            self.App.place_component(save_button, 10, 5, 100, 40)
            self.App.place_component(cancel_button, 120, 5, 70, 40)

    def GetButtons(self):
        # NEW: top buttons by name (used in a few places)
        return {
            "Crop": self.crop_button,
            "Brightness": self.brightness_button,
            "Filters": self.filters_button,
            "Pencil": self.pencil_button,
            "Eraser": self.eraser_button,
            "AI Features": self.ai_features_button
        }

    def ClosePanel(self):
        # NEW: un-highlight the active button, remove the side panel, center the canvas
        current_button = self.App.activeTopButton.get()

        if current_button != "None":
            self.GetButtons()[current_button].config(bg="SystemButtonFace", highlightbackground="black", relief=RAISED)
            self.App.activeTopButton.set("None")

        if self.PanelsFrame:
            self.PanelsFrame.destroy()
            self.PanelsFrame = None

        self.App.canvas_frame.place_configure(x=1520/2-325, y=150)

    def TopButtonClicked(self, button_name):
        current_button = self.App.activeTopButton.get()
        buttons = self.GetButtons()

        # clicking the active button again closes its panel
        if current_button == button_name:
            self.ClosePanel()
            return

        if current_button != "None":
            buttons[current_button].config(bg="SystemButtonFace", highlightbackground="black", relief=RAISED)

        buttons[button_name].config(bg="yellow", highlightbackground="black", relief=RAISED)

        if self.PanelsFrame:
            self.PanelsFrame.destroy()

        self.App.canvas_frame.place_configure(x=1520/2-650, y=150)

        self.PanelsFrame = Frame(self.App.root, bd=1, relief=SOLID, bg="red")
        self.App.place_component(self.PanelsFrame, 1000, 150, 420, 650)

        if button_name == "Crop":
            self.Panel = CropPanel(self.App, self.PanelsFrame)
        elif button_name == "Brightness":
            self.Panel = LightPanel(self.App, self.PanelsFrame)
        elif button_name == "Filters":
            self.Panel = FiltersPanel(self.App, self.PanelsFrame)
        elif button_name == "Pencil":
            self.Panel = DrawingPanel(self.App, self.PanelsFrame)
        elif button_name == "Eraser":
            self.Panel = EraserPanel(self.App, self.PanelsFrame)
        elif button_name == "AI Features":
            self.Panel = AIPanel(self.App, self.PanelsFrame)
        self.Panel.pack(fill=BOTH, expand=True)

        self.App.activeTopButton.set(button_name)

    def SaveClicked(self):
        # NEW: open the save window
        if self.Editor.active_image is None:
            return
        SaveDialog(self.App)

    def CancelClicked(self):
        # NEW: discard the image and go back to the "Open Image" screen
        doc = self.Editor.active_image
        if doc is None:
            return

        if doc.modified:
            answer = messagebox.askyesno(
                "Discard changes?",
                "You have unsaved changes.\nDo you want to discard them and go back?"
            )
            if not answer:
                return

        self.ClosePanel()          # close the side panel first (it uses the canvas)
        self.Editor.CloseImage()   # then remove the image -> back to Open Image screen

    def UpdateButtons(self, *args):
        self.CoreTitleButtons.destroy()
        self.CreateButtons()