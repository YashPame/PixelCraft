from tkinter import *
from tkinter import ttk

LIGHT_OPTIONS = ["Brightness", "Exposure", "Contrast", "Highlights", "Shadows", "Vignette"]
COLOR_OPTIONS = ["Saturation", "Warmth", "Tint", "Sharpness"]


class LightPanel(Frame):
    def __init__(self, App, PanelFrame):
        super().__init__(PanelFrame)
        self.App = App
        self.Editor = App.editor

        self.sliders = {}       # option name -> slider
        self.after_id = None    # small delay while sliding

        Label(self, text="Light", font=("Arial", 16), fg="#2f3775").pack(pady=(20, 10))
        for option in LIGHT_OPTIONS:
            self.CreateOption(option)

        Label(self, text="Color", font=("Arial", 16), fg="#2f3775").pack(pady=(20, 10))
        for option in COLOR_OPTIONS:
            self.CreateOption(option)

        # let the Editor find this panel (used by Undo / Redo / Reset)
        self.App.light_panel = self

        # show the current values if the image was already edited
        if self.Editor.active_image is not None:
            self.SetValues(self.Editor.active_image.adjustments)

    def CreateOption(self, option):
        row = Frame(self)
        row.pack(pady=5)

        Label(row, text=option, font=("Arial", 12), fg="#2f3775", width=12, anchor="w").grid(row=0, column=0, padx=25)

        slider = ttk.Scale(row, from_=-100, to=100, orient=HORIZONTAL, length=200, command=self.OnSlide)
        slider.grid(row=0, column=1, padx=5)
        slider.bind("<ButtonPress-1>", self.StartSlide)
        slider.bind("<ButtonRelease-1>", self.EndSlide)

        self.sliders[option] = slider

    def GetValues(self):
        # ttk.Scale gives floats, the editor wants whole numbers
        return {option: int(round(slider.get())) for option, slider in self.sliders.items()}

    def UpdateImage(self):
        self.after_id = None
        # save_state=False: undo is handled in StartSlide / EndSlide
        # (ApplyAdjustments does nothing if the values did not change)
        self.Editor.ApplyAdjustments(self.GetValues(), save_state=False)

    def OnSlide(self, value):
        # update the image only 30 ms after the slider stops moving
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        self.after_id = self.after(30, self.UpdateImage)

    def StartSlide(self, event):
        self.Editor.StartAdjust()

    def EndSlide(self, event):
        # apply the final value right away, then add one undo step
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        self.UpdateImage()
        self.Editor.EndAdjust()

    def SetValues(self, values):
        # used by Undo / Redo / Reset / Open to move the sliders
        for option, slider in self.sliders.items():
            slider.set(values.get(option, 0))