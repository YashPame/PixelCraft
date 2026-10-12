from tkinter import *
import numpy as np
import cv2


class EraserPanel(Frame):
    def __init__(self, App, PanelFrame):
        self.t = App.theme
        t = self.t
        super().__init__(PanelFrame, bg=t["sidebar"])
        self.App = App
        self.Editor = App.editor
        self.canvas = self.Editor.canvas

        self.strokes = []
        self.mask_shape = None
        self.last_point = None

        Label(self, text="Magic Eraser", font=self.App.adjust_font(16, bold=True),
              bg=t["sidebar"], fg=t["accent"]).pack(anchor="w", padx=20, pady=(18, 0))
        Label(self, text="Paint over what you want to remove", font=self.App.adjust_font(10),
              bg=t["sidebar"], fg=t["muted"]).pack(anchor="w", padx=20, pady=(0, 6))

        section = self.Section(None)
        top_row = Frame(section, bg=t["sidebar"])
        top_row.pack(fill=X)
        Label(top_row, text="Brush Size", font=self.App.adjust_font(11, bold=True),
              bg=t["sidebar"], fg=t["text"]).pack(side=LEFT)
        self.SizeLabel = Label(top_row, text="25", font=self.App.adjust_font(9, bold=True),
                               bg=t["accent_light"], fg=t["accent"], width=4)
        self.SizeLabel.pack(side=RIGHT)

        self.SizeSlider = self.App.CreateSlider(section, from_=5, to=100, length=330,
                                                command=lambda v: self.SizeLabel.config(text=str(int(float(v)))))
        self.SizeSlider.set(25)
        self.SizeSlider.pack(anchor="w", pady=(10, 0))

        section = self.Section("Remove")
        Label(section, text="Paint with the left mouse button over the object. "
                            "Works best on small things like spots, wires, text or small objects.",
              font=self.App.adjust_font(10), bg=t["sidebar"], fg=t["muted"],
              wraplength=self.App.scale_x(320), justify=LEFT).pack(anchor="w", pady=(4, 10))

        buttons = Frame(section, bg=t["sidebar"])
        buttons.pack(fill=X)
        Button(buttons, text="Clear Selection", font=self.App.adjust_font(10, bold=True),
               bg=t["accent_light"], fg=t["accent"], activebackground=t["trough"], activeforeground=t["accent"],
               relief=FLAT, bd=0, pady=6, cursor="hand2", command=self.ClearMask).pack(side=LEFT, expand=True, fill=X, padx=(0, 6))
        Button(buttons, text="Remove", font=self.App.adjust_font(11, bold=True),
               bg=t["accent"], fg="#ffffff", activebackground=t["accent_hover"], activeforeground="#ffffff",
               relief=FLAT, bd=0, pady=6, cursor="hand2", command=self.Remove).pack(side=LEFT, expand=True, fill=X, padx=(6, 0))

        self.canvas.bind("<ButtonPress-1>", self.OnPress)
        self.canvas.bind("<B1-Motion>", self.OnDrag)
        self.canvas.config(cursor="crosshair")

        self.bind("<Destroy>", self.OnDestroy)

        self.App.eraser_panel = self

    def Section(self, title):
        t = self.t
        Frame(self, bg=t["border"], height=1).pack(fill=X, padx=20, pady=(14, 0))
        section = Frame(self, bg=t["sidebar"])
        section.pack(fill=X, padx=20, pady=(12, 0))
        if title:
            Label(section, text=title, font=self.App.adjust_font(11, bold=True),
                  bg=t["sidebar"], fg=t["text"]).pack(anchor="w")
        return section


    def DisplayZoom(self):
        doc = self.Editor.active_image
        if doc is None or self.Editor.display_width == 0:
            return 1.0
        return self.Editor.display_width / doc.image.shape[1]

    def ImagePoint(self, event):
        zoom = self.DisplayZoom()
        x = (self.canvas.canvasx(event.x) - self.Editor.image_x) / zoom
        y = (self.canvas.canvasy(event.y) - self.Editor.image_y) / zoom
        return int(x), int(y)

    def OnPress(self, event):
        doc = self.Editor.active_image
        if doc is None:
            return
        if self.mask_shape != doc.base_image.shape[:2]:
            self.ClearMask()
            self.mask_shape = doc.base_image.shape[:2]

        size = max(1, int(self.SizeSlider.get() / self.DisplayZoom()))
        self.strokes.append(([self.ImagePoint(event)], size))
        self.DrawMask()

    def OnDrag(self, event):
        if self.Editor.active_image is None or not self.strokes:
            return
        self.strokes[-1][0].append(self.ImagePoint(event))
        self.DrawMask()

    def DrawMask(self):
        self.canvas.delete("erase_mask")
        doc = self.Editor.active_image
        if doc is None or doc.base_image.shape[:2] != self.mask_shape:
            self.strokes = []
            return
        zoom = self.DisplayZoom()
        ix, iy = self.Editor.image_x, self.Editor.image_y

        for points, size in self.strokes:
            width = max(1, size * zoom)
            canvas_points = [(ix + x * zoom, iy + y * zoom) for x, y in points]
            if len(canvas_points) == 1:
                (cx, cy), r = canvas_points[0], width / 2
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#ff3b3b", outline="",
                                        stipple="gray50", tags="erase_mask")
            else:
                self.canvas.create_line(*[c for p in canvas_points for c in p], width=width, fill="#ff3b3b",
                                        capstyle=ROUND, joinstyle=ROUND, stipple="gray50", tags="erase_mask")

    def ClearMask(self):
        self.strokes = []
        self.canvas.delete("erase_mask")


    def Remove(self):
        doc = self.Editor.active_image
        if doc is None or not self.strokes:
            return

        h, w = doc.base_image.shape[:2]
        mask = np.zeros((h, w), np.uint8)
        for points, size in self.strokes:
            pts = np.array(points, np.int32)
            if len(pts) == 1:
                cv2.circle(mask, tuple(int(v) for v in pts[0]), max(1, size // 2), 255, -1)
            else:
                cv2.polylines(mask, [pts.reshape(-1, 1, 2)], False, 255, thickness=size)

        self.ClearMask()
        self.Editor.MagicErase(mask)


    def OnDestroy(self, event):
        if event.widget is not self:
            return
        try:
            self.canvas.delete("erase_mask")
            self.canvas.unbind("<ButtonPress-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.config(cursor="")
        except TclError:
            pass
        self.App.eraser_panel = None