from tkinter import *
from tkinter import ttk
from Core.image_editor import Editor


class EditorCanvas(Frame):
    def __init__(self, App):
        t = App.theme                                   # colors from main.py
        super().__init__(App.root)

        self.App = App
        self.CreateScrollbarStyle()

        self.canvas = Canvas(self, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.y_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style="Editor.Vertical.TScrollbar")
        self.y_scrollbar.grid(row=0, column=1, sticky="ns")

        self.x_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview, style="Editor.Horizontal.TScrollbar")
        self.x_scrollbar.grid(row=1, column=0, sticky="ew")

        self.canvas.configure(
            xscrollcommand=lambda first, last: self.AutoHide(self.x_scrollbar, first, last),
            yscrollcommand=lambda first, last: self.AutoHide(self.y_scrollbar, first, last)
        )

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.SetupPanning()                 # Panning: drag the image with the mouse, even when a panel is open

        self.App.editor = Editor(App, self.canvas)

    # ---------------- Scrollbars ----------------

    def CreateScrollbarStyle(self):
        # scrollbar = only a flat thumb on a dark track (no arrows), like modern apps
        t = self.App.theme
        thumb, hover = "#5b6275", "#8a92ab"                       # thumb color, thumb color on hover
        states = [("pressed", t["accent_light"]), ("active", hover)]
        style = ttk.Style()
        for orient, sticky in (("Vertical", "ns"), ("Horizontal", "ew")):
            name = f"Editor.{orient}.TScrollbar"
            # layout without the arrow buttons: only the track and the thumb
            style.layout(name, [(f"{orient}.Scrollbar.trough", {"sticky": sticky,
                         "children": [(f"{orient}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
            # lightcolor / darkcolor = clam's 3D edges; same as the thumb = flat look
            style.configure(name, troughcolor=t["canvas_bg"], bordercolor=t["canvas_bg"], background=thumb, lightcolor=thumb, darkcolor=thumb, gripcount=0, arrowsize=10, relief=FLAT)
            style.map(name, background=states, lightcolor=states, darkcolor=states)

    def AutoHide(self, scrollbar, first, last):
        # Hide the scrollbar when image is visible in that direction
        needed = float(first) > 0.0 or float(last) < 1.0
        shown = scrollbar.winfo_manager() == "grid"            # "" after grid_remove()
        if needed != shown:
            if needed:
                scrollbar.grid()
            else:
                scrollbar.grid_remove()
        scrollbar.set(first, last)

    # ---------------- Drag to move the image ----------------

    def SetupPanning(self):
        # right or middle mouse button: always drags the image
        # left mouse button: drags the image only when no tool panel is using the canvas
        #   (crop / draw / eraser panels use the left button themselves)
        self.panning = False
        self.canvas.bindtags(("Pan",) + self.canvas.bindtags())   # our own tag, panels can't overwrite it
        for button in (1, 2, 3):
            self.canvas.bind_class("Pan", f"<ButtonPress-{button}>", lambda e, b=button: self.StartPan(e, b))
            self.canvas.bind_class("Pan", f"<B{button}-Motion>", self.DoPan)
            self.canvas.bind_class("Pan", f"<ButtonRelease-{button}>", self.EndPan)

    def CanPan(self, button):
        if self.App.editor.active_image is None:
            return False
        if button == 1 and self.canvas.bind("<ButtonPress-1>"):
            return False          # a panel (crop, draw, ...) is using the left button
        # only when the image is bigger than the canvas
        x0, x1 = self.canvas.xview()
        y0, y1 = self.canvas.yview()
        return x0 > 0 or x1 < 1 or y0 > 0 or y1 < 1

    def StartPan(self, event, button):
        self.panning = self.CanPan(button)
        if self.panning:
            self.canvas.scan_mark(event.x, event.y)
            self.canvas.config(cursor="fleur")

    def DoPan(self, event):
        if self.panning:
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    def EndPan(self, event):
        if self.panning:
            self.panning = False
            # back to the panel's cursor (crosshair for draw / crop) or normal
            self.canvas.config(cursor="crosshair" if self.canvas.bind("<ButtonPress-1>") else "")