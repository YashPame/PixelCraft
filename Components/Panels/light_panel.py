from tkinter import *

LIGHT_OPTIONS = ["Brightness", "Exposure", "Contrast", "Highlights", "Shadows", "Vignette"]
COLOR_OPTIONS = ["Saturation", "Warmth", "Tint", "Sharpness"]


class LightPanel(Frame):
    def __init__(self, App, PanelFrame):
        self.t = App.theme                          # colors from main.py
        super().__init__(PanelFrame, bg=self.t["sidebar"])
        self.App = App
        self.Editor = App.editor
        t = self.t

        self.sliders = {}       # option name -> slider
        self.values = {}        # option name -> small label showing the number
        self.after_id = None    # small delay while sliding

        # ----- title -----
        Label(self, text="Light & Color", font=self.App.adjust_font(16, bold=True),
              bg=t["sidebar"], fg=t["accent"]).pack(anchor="w", padx=20, pady=(18, 0))
        Label(self, text="Adjust brightness, tones and colors", font=self.App.adjust_font(10),
              bg=t["sidebar"], fg=t["muted"]).pack(anchor="w", padx=20, pady=(0, 6))

        # ----- Light -----
        section = self.Section("Light")
        for option in LIGHT_OPTIONS:
            self.CreateOption(section, option)

        # ----- Color -----
        section = self.Section("Color")
        for option in COLOR_OPTIONS:
            self.CreateOption(section, option)

        # let the Editor find this panel (used by Undo / Redo / Reset)
        self.App.light_panel = self

        # show the current values if the image was already edited
        if self.Editor.active_image is not None:
            self.SetValues(self.Editor.active_image.adjustments)

    # ---------------- look ----------------

    def Section(self, title):
        # thin line, then a small title, then the section's content
        t = self.t
        Frame(self, bg=t["border"], height=1).pack(fill=X, padx=20, pady=(12, 0))
        section = Frame(self, bg=t["sidebar"])
        section.pack(fill=X, padx=20, pady=(10, 0))
        Label(section, text=title, font=self.App.adjust_font(11, bold=True),
              bg=t["sidebar"], fg=t["text"]).pack(anchor="w", pady=(0, 2))
        return section

    def CreateOption(self, parent, option):
        t = self.t

        # name on the left, value badge on the right, slider below
        top_row = Frame(parent, bg=t["sidebar"])
        top_row.pack(fill=X, pady=(6, 0))
        Label(top_row, text=option, font=self.App.adjust_font(10),
              bg=t["sidebar"], fg=t["text"]).pack(side=LEFT)
        value_label = Label(top_row, text="0", font=self.App.adjust_font(9, bold=True),
                            bg=t["accent_light"], fg=t["accent"], width=4)
        value_label.pack(side=RIGHT)

        slider = self.App.CreateSlider(parent, length=330, command=self.OnSlide)
        slider.pack(anchor="w", pady=(4, 0))
        slider.bind("<ButtonPress-1>", self.StartSlide)
        slider.bind("<ButtonRelease-1>", self.EndSlide)

        self.sliders[option] = slider
        self.values[option] = value_label

    def ShowValues(self):
        # update the small number next to each slider
        for option, slider in self.sliders.items():
            self.values[option].config(text=str(int(round(slider.get()))))

    # ---------------- sliders ----------------

    def GetValues(self):
        # the editor wants whole numbers
        return {option: int(round(slider.get())) for option, slider in self.sliders.items()}

    def UpdateImage(self):
        self.after_id = None
        # save_state=False: undo is handled in StartSlide / EndSlide
        # (ApplyAdjustments does nothing if the values did not change)
        self.Editor.ApplyAdjustments(self.GetValues(), save_state=False)

    def OnSlide(self, value):
        self.ShowValues()
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
        self.ShowValues()