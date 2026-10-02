from tkinter import *
from tkinter import ttk

class LightPanel(Frame):
    def __init__(self, App, PanelFrame):
        super().__init__(PanelFrame)
        self.App = App

        self.LightColorOptionsInstances = {}   # option name -> slider
        self.after_id = None                   # for the small delay while sliding

        # Normal frame that holds all the sliders (no scrolling)
        self.ContentFrame = Frame(self)
        self.ContentFrame.pack(fill=BOTH, expand=True)

        LightLabel = Label(self.ContentFrame, text="Light", font=("Arial", 16), fg="#2f3775")
        LightLabel.pack(pady=(20,10))

        LightOptions = ["Brightness", "Exposure", "Contrast", "Highlights", "Shadows", "Vignette"]
        for option in LightOptions:
            self.CreateOption(option)

        ColorLabel = Label(self.ContentFrame, text="Color", font=("Arial", 16), fg="#2f3775")
        ColorLabel.pack(pady=(20,10))

        ColorOptions = ["Saturation", "Warmth", "Tint", "Sharpness"]
        for option in ColorOptions:
            self.CreateOption(option)

        # Let the Editor find this panel (used by Undo / Redo / Reset)
        self.App.light_panel = self

        # If the panel is opened after editing, show the current values
        editor = getattr(self.App, "editor", None)
        if editor is not None and editor.active_image is not None:
            self.SetValues(editor.active_image.adjustments)

    def CreateOption(self, option):
        optionFrame = Frame(self.ContentFrame)
        optionFrame.pack(pady=5)

        optionLabel = Label(optionFrame, text=option, font=("Arial", 12), fg="#2f3775", width=12, anchor="w")
        optionLabel.grid(row=0, column=0, padx=25, sticky="w")

        optionSlider = ttk.Scale(optionFrame, from_=-100, to=100, orient=HORIZONTAL, length=200)
        optionSlider.set(0)
        optionSlider.config(command=self.OnSlide)   # runs while dragging
        optionSlider.grid(row=0, column=1, padx=5)
        optionSlider.bind("<ButtonPress-1>", self.StartSlide)
        optionSlider.bind("<ButtonRelease-1>", self.EndSlide)

        self.LightColorOptionsInstances[option] = optionSlider

    def UpdateValues(self, event=None):
        self.after_id = None
        Values = {}

        for option, slider in self.LightColorOptionsInstances.items():
            Values[option] = int(round(slider.get()))   # ttk.Scale gives floats

        # save_state=False: undo is handled in StartSlide / EndSlide
        self.App.editor.ApplyAdjustments(Values, save_state=False)

    def OnSlide(self, value):
        # wait 30 ms after the last movement before updating the image
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        self.after_id = self.after(30, self.UpdateValues)

    def StartSlide(self, event):
        self.App.editor.StartAdjust()

    def EndSlide(self, event):
        # apply the final value right away, then record it for undo
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        self.UpdateValues()
        self.App.editor.EndAdjust()

    def SetValues(self, values):
        # used by Undo / Redo / Reset / Open to move the sliders
        for option, slider in self.LightColorOptionsInstances.items():
            slider.set(values.get(option, 0))