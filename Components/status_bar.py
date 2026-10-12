import os
from tkinter import *


class StatusBar(Frame):
    def __init__(self, App):
        self.t = App.theme                              
        t = self.t
        super().__init__(App.root, bg=t["surface"])
        self.App = App
        self.Editor = App.editor
        self.file_sizes = {}                            

        Frame(self, bg=t["border"], height=1).pack(side=TOP, fill=X)
        row = Frame(self, bg=t["surface"])
        row.pack(fill=BOTH, expand=True, padx=16)

        self.position = self.Item(row, "Cursor", LEFT)
        self.swatch = Frame(row, bg=t["surface"], width=12, height=12,
                            highlightthickness=1, highlightbackground=t["border"])
        self.swatch.pack(side=LEFT, padx=(0, 6))
        self.color = self.Item(row, "RGB", LEFT, divider=False)
        self.hex = self.Item(row, "HEX", LEFT)

        self.state = Label(row, text="", font=self.App.adjust_font(9, bold=True), bg=t["surface"])
        self.state.pack(side=RIGHT)
        self.Divider(row, RIGHT)
        self.zoom = self.Item(row, "Zoom", RIGHT)
        self.size = self.Item(row, "Size", RIGHT)
        self.file = self.Item(row, "File", RIGHT, divider=False)

        self.App.root.bind_all("<Motion>", self.OnMouseMove, add="+")
        self.Editor.canvas.bind("<Leave>", lambda e: self.ClearCursor(), add="+")

        self.ClearCursor()
        self.Refresh()

    def Resize(self, panel_open):
        x, y, w, h = self.App.STATUS
        if panel_open:
            w -= self.App.SIDEBAR[2]
        self.App.place_component(self, x, y, w, h)


    def Item(self, parent, title, side, divider=True):
        t = self.t
        box = Frame(parent, bg=t["surface"])
        Label(box, text=title, font=self.App.adjust_font(9), bg=t["surface"], fg=t["muted"]).pack(side=LEFT, padx=(0, 5))
        value = Label(box, text="", font=self.App.adjust_font(9, bold=True), bg=t["surface"], fg=t["text"])
        value.pack(side=LEFT)

        if side == LEFT:
            box.pack(side=LEFT)
            if divider:
                self.Divider(parent, LEFT)
        else:
            box.pack(side=RIGHT)
            if divider:
                self.Divider(parent, RIGHT)
        return value

    def Divider(self, parent, side):
        Frame(parent, bg=self.t["border"], width=1, height=14).pack(side=side, padx=12)


    def OnMouseMove(self, event):
        canvas = self.Editor.canvas
        doc = self.Editor.active_image
        if event.widget is not canvas or doc is None or self.Editor.display_width == 0:
            return

        image = doc.image
        h, w = image.shape[:2]
        zoom = self.Editor.display_width / w
        x = int((canvas.canvasx(event.x) - self.Editor.image_x) / zoom)
        y = int((canvas.canvasy(event.y) - self.Editor.image_y) / zoom)

        if not (0 <= x < w and 0 <= y < h):
            self.ClearCursor()
            return

        pixel = image[y, x]
        if image.ndim == 2:                         
            r = g = b = int(pixel)
            alpha = None
        else:                                       
            b, g, r = (int(v) for v in pixel[:3])
            alpha = int(pixel[3]) if image.shape[2] == 4 else None

        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.position.config(text=f"{x}, {y}")
        self.color.config(text=f"{r}, {g}, {b}" + (f"  ·  A {alpha}" if alpha is not None else ""))
        self.hex.config(text=hex_color.upper())
        self.swatch.config(bg=hex_color)

    def ClearCursor(self):
        self.position.config(text="—")
        self.color.config(text="—")
        self.hex.config(text="—")
        self.swatch.config(bg=self.t["surface"])


    def FileSize(self, path):
        if path not in self.file_sizes:
            try:
                size = os.path.getsize(path)
                self.file_sizes[path] = f"{size / 1024:.0f} KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f} MB"
            except OSError:
                self.file_sizes[path] = ""
        return self.file_sizes[path]

    def Refresh(self):
        t = self.t
        doc = self.Editor.active_image

        if doc is None:
            self.file.config(text="No image open")
            self.size.config(text="—")
            self.zoom.config(text="—")
            self.state.config(text="")
        else:
            h, w = doc.image.shape[:2]
            channels = 1 if doc.image.ndim == 2 else doc.image.shape[2]
            kind = {1: "Gray", 3: "RGB", 4: "RGBA"}.get(channels, "")
            file_size = self.FileSize(doc.file_path)

            self.file.config(text=doc.file_name + (f"  ·  {file_size}" if file_size else ""))
            self.size.config(text=f"{w} × {h} px  ·  {kind}")
            self.zoom.config(text=doc.zoom_percentage.get())
            if doc.modified:
                self.state.config(text="●  Unsaved changes", fg=t["warning"])
            else:
                self.state.config(text="●  No changes", fg=t["success"])

        self.after(500, self.Refresh)