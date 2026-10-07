from tkinter import *
from tkinter import ttk


class CropPanel(Frame):
    def __init__(self, App, PanelFrame):
        self.t = App.theme                          # colors from main.py
        super().__init__(PanelFrame, bg=self.t["sidebar"])
        self.App = App
        self.Editor = App.editor
        self.canvas = self.Editor.canvas
        t = self.t

        # crop box as fractions of the image (0 to 1): [left, top, right, bottom]
        # None = no box drawn yet
        self.box = None
        self.start_x = 0
        self.start_y = 0

        # ----- title -----
        Label(self, text="Crop & Rotate", font=self.App.adjust_font(16, bold=True),
              bg=t["sidebar"], fg=t["accent"]).pack(anchor="w", padx=20, pady=(18, 0))
        Label(self, text="Rotate, flip, straighten and crop", font=self.App.adjust_font(10),
              bg=t["sidebar"], fg=t["muted"]).pack(anchor="w", padx=20, pady=(0, 6))

        # ----- Rotate | Flip (two centered halves with a line between) -----
        section = self.Section(None)
        section.grid_columnconfigure(0, weight=1)   # left half and right half share the width
        section.grid_columnconfigure(2, weight=1)
        rotate_half = Frame(section, bg=t["sidebar"])
        rotate_half.grid(row=0, column=0)
        Frame(section, bg=t["border"], width=1).grid(row=0, column=1, sticky="ns")
        flip_half = Frame(section, bg=t["sidebar"])
        flip_half.grid(row=0, column=2)

        self.SmallTitle(rotate_half, "Rotate").grid(row=0, column=0, columnspan=2, pady=(0, 6))
        self.IconButton(rotate_half, self.App.IconImage_RotateLeft, self.RotateLeft).grid(row=1, column=0, padx=(0, 8))
        self.IconButton(rotate_half, self.App.IconImage_RotateRight, self.RotateRight).grid(row=1, column=1)

        self.SmallTitle(flip_half, "Flip").grid(row=0, column=0, columnspan=2, pady=(0, 6))
        self.IconButton(flip_half, self.App.IconImage_FlipHorizontal, self.FlipHorizontal).grid(row=1, column=0, padx=(0, 8))
        self.IconButton(flip_half, self.App.IconImage_FlipVertical, self.FlipVertical).grid(row=1, column=1)

        # ----- Straighten: angle value, slider and reset -----
        section = self.Section(None)
        top_row = Frame(section, bg=t["sidebar"])
        top_row.pack(fill=X)
        self.SmallTitle(top_row, "Straighten").pack(side=LEFT)
        self.AngleLabel = Label(top_row, text="0.0°", font=self.App.adjust_font(10, bold=True),
                                bg=t["accent_light"], fg=t["accent"], padx=8)
        self.AngleLabel.pack(side=RIGHT)

        slider_row = Frame(section, bg=t["sidebar"])
        slider_row.pack(fill=X, pady=(10, 0))

        self.AngleSlider = self.App.CreateSlider(slider_row, from_=-45, to=45, resolution=0.5)
        if self.Editor.active_image is not None:
            self.AngleSlider.set(self.Editor.active_image.straighten_angle)
            self.ShowAngle(self.Editor.active_image.straighten_angle)
        self.AngleSlider.config(command=self.OnSlide)
        self.AngleSlider.bind("<ButtonPress-1>", self.StartSlide)
        self.AngleSlider.bind("<ButtonRelease-1>", self.EndSlide)
        self.AngleSlider.pack(side=LEFT)

        Button(slider_row, text="Reset", font=self.App.adjust_font(10, bold=True),
               bg=t["accent_light"], fg=t["accent"], activebackground=t["trough"], activeforeground=t["accent"],
               relief=FLAT, bd=0, padx=10, pady=2, cursor="hand2",
               command=self.ResetAngle).pack(side=RIGHT)

        # ----- Crop -----
        section = self.Section("Crop")
        Label(section, text="Click and drag on the image to select the area", font=self.App.adjust_font(10),
              bg=t["sidebar"], fg=t["muted"], wraplength=self.App.scale_x(290), justify=LEFT).pack(anchor="w", pady=(4, 10))
        Button(section, text="Apply Crop", font=self.App.adjust_font(11, bold=True),
               bg=t["accent"], fg="#ffffff", activebackground=t["accent_hover"], activeforeground="#ffffff",
               relief=FLAT, bd=0, pady=6, cursor="hand2", command=self.ApplyCrop).pack(fill=X)

        # mouse on the image draws the crop box
        self.canvas.bind("<ButtonPress-1>", self.OnPress)
        self.canvas.bind("<B1-Motion>", self.OnDrag)

        # clean up when the panel is closed
        self.bind("<Destroy>", self.OnDestroy)

        # let the Editor find this panel (it calls DrawCropBox and SetAngle)
        self.App.crop_panel = self

    # ---------------- look ----------------

    def Section(self, title):
        # thin line, then (optional) title, then the section's content
        t = self.t
        Frame(self, bg=t["border"], height=1).pack(fill=X, padx=20, pady=(14, 0))
        section = Frame(self, bg=t["sidebar"])
        section.pack(fill=X, padx=20, pady=(12, 0))
        if title:
            self.SmallTitle(section, title).pack(anchor="w")
        return section

    def SmallTitle(self, parent, text):
        return Label(parent, text=text, font=self.App.adjust_font(11, bold=True), bg=self.t["sidebar"], fg=self.t["text"])

    def ShowAngle(self, angle):
        self.AngleLabel.config(text=f"{float(angle):.1f}°")

    def IconButton(self, parent, icon, command):
        t = self.t
        return Button(parent, image=icon, command=command, bg=t["accent_light"], activebackground=t["trough"],
                      relief=FLAT, bd=0, padx=6, pady=6, cursor="hand2")

    # ---------------- Rotate / Flip ----------------

    def RotateLeft(self):
        self.box = None
        self.Editor.Rotate90(clockwise=False)

    def RotateRight(self):
        self.box = None
        self.Editor.Rotate90(clockwise=True)

    def FlipHorizontal(self):
        self.box = None
        self.Editor.Flip(horizontal=True)

    def FlipVertical(self):
        self.box = None
        self.Editor.Flip(horizontal=False)

    # ---------------- Straighten ----------------

    def StartSlide(self, event):
        self.Editor.StartAdjust()           # remember the image for undo

    def OnSlide(self, value):
        self.ShowAngle(value)
        self.Editor.Straighten(round(float(value), 1))

    def EndSlide(self, event):
        self.Editor.EndAdjust()             # add one undo step

    def ResetAngle(self):
        self.Editor.StartAdjust()
        self.Editor.Straighten(0)
        self.Editor.EndAdjust()
        self.AngleSlider.set(0)
        self.ShowAngle(0)

    def SetAngle(self, angle):
        # used by Undo / Redo / Reset
        self.AngleSlider.set(angle)
        self.ShowAngle(angle)

    # ---------------- Crop box ----------------

    def ToFraction(self, event):
        # mouse position -> position inside the image as 0 to 1 (kept inside the image)
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        fx = (x - self.Editor.image_x) / self.Editor.display_width
        fy = (y - self.Editor.image_y) / self.Editor.display_height

        fx = min(max(fx, 0), 1)
        fy = min(max(fy, 0), 1)
        return fx, fy

    def OnPress(self, event):
        if self.Editor.active_image is None:
            return
        self.start_x, self.start_y = self.ToFraction(event)
        self.box = None
        self.DrawCropBox()

    def OnDrag(self, event):
        if self.Editor.active_image is None:
            return
        x, y = self.ToFraction(event)

        left = min(self.start_x, x)
        right = max(self.start_x, x)
        top = min(self.start_y, y)
        bottom = max(self.start_y, y)

        self.box = [left, top, right, bottom]
        self.DrawCropBox()

    def DrawCropBox(self):
        # the Editor calls this after redrawing the image (zoom, undo, ...)
        self.canvas.delete("cropbox")
        if self.box is None or self.Editor.active_image is None:
            return

        left, top, right, bottom = self.box
        ix, iy = self.Editor.image_x, self.Editor.image_y
        iw, ih = self.Editor.display_width, self.Editor.display_height

        self.canvas.create_rectangle(ix + left * iw, iy + top * ih,
                                     ix + right * iw, iy + bottom * ih,
                                     outline="white", width=2, dash=(6, 4), tags="cropbox")

    def ApplyCrop(self):
        if self.box is None:
            return
        left, top, right, bottom = self.box
        self.box = None
        self.Editor.Crop(left, top, right, bottom)   # Editor ignores a box that is too small
        self.DrawCropBox()

    # ---------------- Closing ----------------

    def OnDestroy(self, event):
        if event.widget is not self:
            return
        try:
            self.canvas.delete("cropbox")
            self.canvas.unbind("<ButtonPress-1>")
            self.canvas.unbind("<B1-Motion>")
        except TclError:
            pass   # canvas already gone (app closing)
        self.App.crop_panel = None