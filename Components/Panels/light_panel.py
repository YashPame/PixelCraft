from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import filedialog

class LightPanel(Frame):
    def __init__(self, App, PanelFrame):
        super().__init__(PanelFrame)
        self.App = App

        self.LightColorOptionsInstances = {}   # option name -> slider
        self.ValueLabels = {}                  # option name -> label showing the number
        self.after_id = None                   # for the small delay while sliding

        self.Canvas = Canvas(self, highlightthickness=0)
        self.ScrollableFrame = Frame(self.Canvas)

        self.ScrollableFrame.bind("<Configure>", lambda e: self.Canvas.configure(scrollregion=self.Canvas.bbox("all")))
        self.Canvas.create_window((0, 0), window=self.ScrollableFrame, anchor="nw")

        self.Canvas.pack(side=LEFT, fill=BOTH, expand=True)

        LightLabel = Label(self.ScrollableFrame, text="Light", font=("Arial", 16), fg="#2f3775")
        LightLabel.pack(pady=5)

        LightOptions = ["Brightness", "Exposure", "Contrast", "Highlights", "Shadows", "Vignette"]
        for option in LightOptions:
            self.CreateOption(option)

        ColorLabel = Label(self.ScrollableFrame, text="Color", font=("Arial", 16), fg="#2f3775")
        ColorLabel.pack(pady=5)

        ColorOptions = ["Saturation", "Warmth", "Tint", "Sharpness"]
        for option in ColorOptions:
            self.CreateOption(option)

        self.Canvas.bind_all("<MouseWheel>", self.Scroll)

        # NEW: let the Editor find this panel (used by Undo / Redo / Reset)
        self.App.light_panel = self

        # NEW: if the panel is opened after editing, show the current values
        editor = getattr(self.App, "editor", None)
        if editor is not None and editor.active_image is not None:
            self.SetValues(editor.active_image.adjustments)

    def CreateOption(self, option):
        optionFrame = Frame(self.ScrollableFrame)
        optionFrame.pack(pady=5)

        optionLabel = Label(optionFrame, text=option, font=("Arial", 12), fg="#2f3775", width=12, anchor="w")
        optionLabel.grid(row=0, column=0, padx=25, sticky="w")

        optionSlider = ttk.Scale(optionFrame, from_=-100, to=100, orient=HORIZONTAL, length=200)
        optionSlider.set(0)
        # runs while dragging; "name=option" remembers which slider it is
        optionSlider.config(command=lambda value, name=option: self.OnSlide(name, value))
        optionSlider.grid(row=0, column=1, padx=5)
        optionSlider.bind("<ButtonPress-1>", self.StartSlide)
        optionSlider.bind("<ButtonRelease-1>", self.EndSlide)

        valueLabel = Label(optionFrame, text="0", width=4, font=("Arial", 10), fg="#2f3775")
        valueLabel.grid(row=0, column=2)

        self.LightColorOptionsInstances[option] = optionSlider
        self.ValueLabels[option] = valueLabel

    def UpdateValues(self, event=None):
        self.after_id = None
        Values = {}

        for option, slider in self.LightColorOptionsInstances.items():
            Values[option] = int(round(slider.get()))   # ttk.Scale gives floats

        # save_state=False: undo is handled in StartSlide / EndSlide
        self.App.editor.ApplyAdjustments(Values, save_state=False)

    def OnSlide(self, name, value):
        # show the number next to the slider
        self.ValueLabels[name].config(text=str(int(round(float(value)))))

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
            value = values.get(option, 0)
            slider.set(value)
            self.ValueLabels[option].config(text=str(value))

    def Scroll(self, event):
        self.Canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")