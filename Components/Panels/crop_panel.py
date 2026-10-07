from tkinter import *
from tkinter import ttk


class CropPanel(Frame):
    def __init__(self, App, PanelFrame):
        super().__init__(PanelFrame)
        self.App = App
        self.Editor = App.editor
        self.canvas = self.Editor.canvas

        # crop box as fractions of the image (0 to 1): [left, top, right, bottom]
        # None = no box drawn yet
        self.box = None
        self.start_x = 0
        self.start_y = 0

        Label(self, text="Crop & Rotate", font=("Arial", 16), fg="#2f3775").pack(pady=10)

        # ----- Rotate -----
        Label(self, text="Rotate", font=("Arial", 12), fg="#2f3775").pack(pady=(15, 0))
        rotate_frame = Frame(self)
        rotate_frame.pack(pady=5)
        Button(rotate_frame, image=self.App.IconImage_RotateLeft, width=30, command=self.RotateLeft).grid(row=0, column=0, padx=5)
        Button(rotate_frame, image=self.App.IconImage_RotateRight, width=30, command=self.RotateRight).grid(row=0, column=1, padx=5)

        # ----- Flip -----
        Label(self, text="Flip", font=("Arial", 12), fg="#2f3775").pack(pady=(15, 0))
        flip_frame = Frame(self)
        flip_frame.pack(pady=5)
        Button(flip_frame, image=self.App.IconImage_FlipHorizontal, width=30, command=self.FlipHorizontal).grid(row=0, column=0, padx=5)
        Button(flip_frame, image=self.App.IconImage_FlipVertical, width=30, command=self.FlipVertical).grid(row=0, column=1, padx=5)

        # ----- Straighten: slider + reset button in one row -----
        Label(self, text="Straighten", font=("Arial", 12), fg="#2f3775").pack(pady=(15, 0))
        straighten_frame = Frame(self)
        straighten_frame.pack(pady=5)

        self.AngleSlider = ttk.Scale(straighten_frame, from_=-45, to=45, orient=HORIZONTAL, length=250)
        if self.Editor.active_image is not None:
            self.AngleSlider.set(self.Editor.active_image.straighten_angle)
        self.AngleSlider.config(command=self.OnSlide)
        self.AngleSlider.bind("<ButtonPress-1>", self.StartSlide)
        self.AngleSlider.bind("<ButtonRelease-1>", self.EndSlide)
        self.AngleSlider.grid(row=0, column=0, padx=5)

        Button(straighten_frame, text="Reset", font=("Arial", 11), command=self.ResetAngle).grid(row=0, column=1, padx=5)

        # ----- Crop -----
        Label(self, text="Crop", font=("Arial", 12), fg="#2f3775").pack(pady=(15, 0))
        Label(self, text="Click and drag on the image to select the area",
              font=("Arial", 10), fg="gray").pack()
        Button(self, text="Apply Crop", font=("Arial", 11, "bold"), width=14,
               bg="#2f3775", fg="white", command=self.ApplyCrop).pack(pady=10)

        # mouse on the image draws the crop box
        self.canvas.bind("<ButtonPress-1>", self.OnPress)
        self.canvas.bind("<B1-Motion>", self.OnDrag)

        # clean up when the panel is closed
        self.bind("<Destroy>", self.OnDestroy)

        # let the Editor find this panel (it calls DrawCropBox and SetAngle)
        self.App.crop_panel = self

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
        self.Editor.Straighten(round(float(value), 1))

    def EndSlide(self, event):
        self.Editor.EndAdjust()             # add one undo step

    def ResetAngle(self):
        self.Editor.StartAdjust()
        self.Editor.Straighten(0)
        self.Editor.EndAdjust()
        self.AngleSlider.set(0)

    def SetAngle(self, angle):
        # used by Undo / Redo / Reset
        self.AngleSlider.set(angle)

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