from tkinter import *
from tkinter import ttk

HANDLE_SIZE = 10    # how close (in pixels) you must click to grab a corner
MIN_BOX = 0.05      # smallest crop box = 5% of the image

class CropPanel(Frame):
    def __init__(self, App, PanelFrame):
        super().__init__(PanelFrame)
        self.App = App
        self.Editor = App.editor
        self.canvas = self.Editor.canvas

        # Crop box as fractions of the image: [left, top, right, bottom], 0 to 1.
        # Fractions keep the box correct even when you zoom.
        self.box = [0.0, 0.0, 1.0, 1.0]
        self.drag_mode = None     # "tl", "tr", "bl", "br" (corners) or "move"
        self.last_x = 0
        self.last_y = 0
        self.after_id = None      # for the small delay while sliding

        self.ContentFrame = Frame(self)
        self.ContentFrame.pack(fill=BOTH, expand=True)

        title = Label(self.ContentFrame, text="Crop & Rotate", font=("Arial", 16), fg="#2f3775")
        title.pack(pady=10)

        # ----- Rotate -----
        self.SectionLabel("Rotate")
        rotateFrame = Frame(self.ContentFrame)
        rotateFrame.pack(pady=5)

        Button(rotateFrame, text="↺  Left", font=("Arial", 11), width=14,
               command=self.RotateLeft).grid(row=0, column=0, padx=5)
        Button(rotateFrame, text="↻  Right", font=("Arial", 11), width=14,
               command=self.RotateRight).grid(row=0, column=1, padx=5)

        # ----- Flip -----
        self.SectionLabel("Flip")
        flipFrame = Frame(self.ContentFrame)
        flipFrame.pack(pady=5)

        Button(flipFrame, text="⇆  Horizontal", font=("Arial", 11), width=14,
               command=self.FlipHorizontal).grid(row=0, column=0, padx=5)
        Button(flipFrame, text="⇅  Vertical", font=("Arial", 11), width=14,
               command=self.FlipVertical).grid(row=0, column=1, padx=5)

        # ----- Straighten (rotate by any angle) -----
        self.SectionLabel("Straighten")

        self.AngleSlider = ttk.Scale(self.ContentFrame, from_=-45, to=45, orient=HORIZONTAL, length=300)
        if self.Editor.active_image is not None:
            self.AngleSlider.set(self.Editor.active_image.straighten_angle)
        self.AngleSlider.config(command=self.OnSlide)
        self.AngleSlider.pack(pady=5)
        self.AngleSlider.bind("<ButtonPress-1>", self.StartSlide)
        self.AngleSlider.bind("<ButtonRelease-1>", self.EndSlide)

        Button(self.ContentFrame, text="Reset Angle", font=("Arial", 11), width=14,
               command=self.ResetAngle).pack(pady=5)

        # ----- Crop -----
        self.SectionLabel("Crop")
        hint = Label(self.ContentFrame, text="Drag the corners or the box on the image",
                     font=("Arial", 10), fg="gray")
        hint.pack()

        cropFrame = Frame(self.ContentFrame)
        cropFrame.pack(pady=10)

        Button(cropFrame, text="Reset Box", font=("Arial", 11), width=14,
               command=self.ResetBox).grid(row=0, column=0, padx=5)
        Button(cropFrame, text="Apply Crop", font=("Arial", 11, "bold"), width=14,
               bg="#2f3775", fg="white", command=self.ApplyCrop).grid(row=0, column=1, padx=5)

        # Mouse on the image canvas moves / resizes the crop box
        self.canvas.bind("<ButtonPress-1>", self.OnPress)
        self.canvas.bind("<B1-Motion>", self.OnDrag)
        self.canvas.bind("<ButtonRelease-1>", self.OnRelease)

        # Clean up the canvas when this panel is closed
        self.bind("<Destroy>", self.OnDestroy)

        # Let the Editor find this panel (to redraw the box and sync the slider)
        self.App.crop_panel = self
        self.DrawCropBox()

    def SectionLabel(self, text):
        label = Label(self.ContentFrame, text=text, font=("Arial", 12), fg="#2f3775")
        label.pack(pady=(15, 0))

    # ---------------- Rotate / Flip buttons ----------------

    def RotateLeft(self):
        self.Editor.Rotate90(clockwise=False)
        self.ResetBox()

    def RotateRight(self):
        self.Editor.Rotate90(clockwise=True)
        self.ResetBox()

    def FlipHorizontal(self):
        self.Editor.Flip(horizontal=True)
        self.ResetBox()

    def FlipVertical(self):
        self.Editor.Flip(horizontal=False)
        self.ResetBox()

    # ---------------- Straighten slider ----------------

    def OnSlide(self, value):
        # wait 30 ms after the last movement before rotating
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        self.after_id = self.after(30, self.UpdateAngle)

    def UpdateAngle(self):
        self.after_id = None
        angle = round(float(self.AngleSlider.get()), 1)
        self.Editor.Straighten(angle)

    def StartSlide(self, event):
        self.Editor.StartAdjust()

    def EndSlide(self, event):
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        self.UpdateAngle()
        self.Editor.EndAdjust()

    def ResetAngle(self):
        self.Editor.StartAdjust()
        self.Editor.Straighten(0)
        self.Editor.EndAdjust()
        self.AngleSlider.set(0)

    def SetAngle(self, angle):
        # used by Undo / Redo / Reset
        self.AngleSlider.set(angle)

    # ---------------- Crop box ----------------

    def ResetBox(self):
        self.box = [0.0, 0.0, 1.0, 1.0]
        self.DrawCropBox()

    def ApplyCrop(self):
        if self.box == [0.0, 0.0, 1.0, 1.0]:
            return   # nothing to crop
        left, top, right, bottom = self.box
        self.Editor.Crop(left, top, right, bottom)
        self.ResetBox()

    def BoxOnCanvas(self):
        # convert the box fractions to canvas pixel positions
        ix, iy = self.Editor.image_x, self.Editor.image_y
        iw, ih = self.Editor.display_width, self.Editor.display_height
        left, top, right, bottom = self.box
        return ix + left * iw, iy + top * ih, ix + right * iw, iy + bottom * ih

    def DrawCropBox(self):
        self.canvas.delete("cropbox")
        if self.Editor.active_image is None:
            return

        x1, y1, x2, y2 = self.BoxOnCanvas()
        ix, iy = self.Editor.image_x, self.Editor.image_y
        iw, ih = self.Editor.display_width, self.Editor.display_height

        # darken the parts that will be cut away
        outside = [
            (ix, iy, ix + iw, y1),        # top
            (ix, y2, ix + iw, iy + ih),   # bottom
            (ix, y1, x1, y2),             # left
            (x2, y1, ix + iw, y2),        # right
        ]
        for rect in outside:
            self.canvas.create_rectangle(*rect, fill="black", stipple="gray50",
                                         outline="", tags="cropbox")

        # rule-of-thirds grid lines
        for i in (1, 2):
            gx = x1 + (x2 - x1) * i / 3
            gy = y1 + (y2 - y1) * i / 3
            self.canvas.create_line(gx, y1, gx, y2, fill="white", dash=(4, 4), tags="cropbox")
            self.canvas.create_line(x1, gy, x2, gy, fill="white", dash=(4, 4), tags="cropbox")

        # border
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="white", width=2, tags="cropbox")

        # corner handles
        s = HANDLE_SIZE / 2
        for cx, cy in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
            self.canvas.create_rectangle(cx - s, cy - s, cx + s, cy + s,
                                         fill="white", outline="#2f3775", tags="cropbox")

    # ---------------- Mouse on the canvas ----------------

    def OnPress(self, event):
        # canvasx/canvasy handle the canvas being scrolled
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        x1, y1, x2, y2 = self.BoxOnCanvas()

        corners = {"tl": (x1, y1), "tr": (x2, y1), "bl": (x1, y2), "br": (x2, y2)}

        self.drag_mode = None
        for name, (cx, cy) in corners.items():
            if abs(x - cx) <= HANDLE_SIZE and abs(y - cy) <= HANDLE_SIZE:
                self.drag_mode = name       # grabbed a corner
                break

        if self.drag_mode is None and x1 < x < x2 and y1 < y < y2:
            self.drag_mode = "move"         # grabbed the inside of the box

        self.last_x, self.last_y = x, y

    def OnDrag(self, event):
        if self.drag_mode is None or self.Editor.display_width == 0:
            return

        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        iw, ih = self.Editor.display_width, self.Editor.display_height
        left, top, right, bottom = self.box

        if self.drag_mode == "move":
            # how far the mouse moved, as a fraction of the image
            dx = (x - self.last_x) / iw
            dy = (y - self.last_y) / ih

            # don't let the box leave the image
            dx = max(-left, min(dx, 1 - right))
            dy = max(-top, min(dy, 1 - bottom))

            left, right = left + dx, right + dx
            top, bottom = top + dy, bottom + dy
        else:
            # mouse position as a fraction of the image
            fx = (x - self.Editor.image_x) / iw
            fy = (y - self.Editor.image_y) / ih

            # move only the sides that belong to the grabbed corner
            if "l" in self.drag_mode:
                left = max(0, min(fx, right - MIN_BOX))
            if "r" in self.drag_mode:
                right = min(1, max(fx, left + MIN_BOX))
            if "t" in self.drag_mode:
                top = max(0, min(fy, bottom - MIN_BOX))
            if "b" in self.drag_mode:
                bottom = min(1, max(fy, top + MIN_BOX))

        self.box = [left, top, right, bottom]
        self.last_x, self.last_y = x, y
        self.DrawCropBox()

    def OnRelease(self, event):
        self.drag_mode = None

    # ---------------- Closing the panel ----------------

    def OnDestroy(self, event):
        if event.widget is not self:
            return

        # When the whole app is closing, the canvas may already be destroyed
        try:
            if self.canvas.winfo_exists():
                self.canvas.delete("cropbox")
                self.canvas.unbind("<ButtonPress-1>")
                self.canvas.unbind("<B1-Motion>")
                self.canvas.unbind("<ButtonRelease-1>")
        except TclError:
            pass

        if getattr(self.App, "crop_panel", None) is self:
            self.App.crop_panel = None