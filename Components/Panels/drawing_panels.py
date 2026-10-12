from tkinter import *
from tkinter import colorchooser

# size_mul: brush size = Size slider x size_mul
TOOLS = {
    "Pen":         {"size_mul": 1.0, "opacity": 1.0},
    "Pencil":      {"size_mul": 0.5, "opacity": 0.75},
    "Marker":      {"size_mul": 2.0, "opacity": 0.9},
    "Highlighter": {"size_mul": 4.0, "opacity": 0.35},
    "Eraser":      {"size_mul": 3.0, "opacity": 1.0},
}

COLORS = ["#000000", "#ffffff", "#e53935", "#fb8c00", "#fdd835", "#43a047",
          "#00acc1", "#1e88e5", "#3949ab", "#8e24aa", "#d81b60", "#6d4c41"]

THEME = "#2f3775"

PREVIEW_WIDTH = 300
PREVIEW_HEIGHT = 80
MAX_PREVIEW_SIZE = PREVIEW_HEIGHT - 16     # biggest brush the preview box can show


class DrawingPanel(Frame):
    def __init__(self, App, PanelFrame, start_tool="Pen"):
        self.t = App.theme                              # colors from main.py
        t = self.t
        super().__init__(PanelFrame, bg=t["sidebar"])
        self.App = App
        self.Editor = App.editor
        self.canvas = self.Editor.canvas

        self.tool = StringVar(value=start_tool)
        self.color = "#e53935"
        self.points = []          # current stroke in IMAGE pixels
        self.last_point = None    # last mouse position on the CANVAS (for the preview line)
        self.swatches = {}        # color -> swatch widget
        self.zoom_trace = None    # so the preview updates when you zoom

        self.ContentFrame = Frame(self, bg=t["sidebar"])
        self.ContentFrame.pack(fill=BOTH, expand=True)

        title = Label(self.ContentFrame, text="Draw", font=self.App.adjust_font(16, bold=True),
                      bg=t["sidebar"], fg=t["accent"])
        title.pack(anchor="w", padx=20, pady=(18, 0))
        Label(self.ContentFrame, text="Pick a tool, size and color", font=self.App.adjust_font(10),
              bg=t["sidebar"], fg=t["muted"]).pack(anchor="w", padx=20, pady=(0, 6))

        # ----- Tools -----
        self.SectionLabel("Tool")
        toolFrame = Frame(self.ContentFrame, bg=t["sidebar"])
        toolFrame.pack(pady=5)

        for index, name in enumerate(TOOLS):
            row, col = divmod(index, 3)
            # Radiobutton with indicatoron=0 looks like a toggle button
            button = Radiobutton(toolFrame, text=name, variable=self.tool, value=name,
                                 indicatoron=0, width=10, font=self.App.adjust_font(10, bold=True),
                                 bg=t["surface"], fg=t["text"], selectcolor=t["accent_light"],
                                 activebackground=t["accent_light"], activeforeground=t["accent"],
                                 relief=FLAT, offrelief=FLAT, bd=0, pady=5, cursor="hand2",
                                 highlightthickness=1, highlightbackground=t["border"],
                                 command=self.UpdatePreview)
            button.grid(row=row, column=col, padx=4, pady=4)

        # ----- Size -----
        self.SectionLabel("Size")
        self.SizeSlider = self.App.CreateSlider(self.ContentFrame, from_=1, to=50, length=300)
        self.SizeSlider.set(5)
        self.SizeSlider.pack(pady=(8, 5))

        # live preview of the brush (same size as it will look on the image)
        self.Preview = Canvas(self.ContentFrame, width=PREVIEW_WIDTH, height=PREVIEW_HEIGHT, bg=t["surface"],
                              highlightthickness=1, highlightbackground=t["border"])
        self.Preview.pack(pady=(5, 0))

        self.PreviewNote = Label(self.ContentFrame, text="", font=self.App.adjust_font(9),
                                 bg=t["sidebar"], fg=t["muted"])
        self.PreviewNote.pack()

        # attach the command only now, after the Preview box exists
        self.SizeSlider.config(command=lambda value: self.UpdatePreview())

        # ----- Colors -----
        self.SectionLabel("Color")
        colorFrame = Frame(self.ContentFrame, bg=t["sidebar"])
        colorFrame.pack(pady=5)

        self.normal_color = t["sidebar"]

        for index, color in enumerate(COLORS):
            row, col = divmod(index, 6)
            swatch = Label(colorFrame, bg=color, width=3, height=1, relief=SOLID, bd=1,
                           highlightthickness=3, highlightbackground=self.normal_color, cursor="hand2")
            swatch.grid(row=row, column=col, padx=3, pady=3)
            swatch.bind("<Button-1>", lambda e, c=color: self.SetColor(c))
            self.swatches[color] = swatch

        Button(self.ContentFrame, text="Custom Color...", font=self.App.adjust_font(10, bold=True), width=16,
               bg=t["accent_light"], fg=t["accent"], activebackground=t["trough"], activeforeground=t["accent"],
               relief=FLAT, bd=0, pady=4, cursor="hand2",
               command=self.PickCustomColor).pack(pady=5)

        # ----- Clear -----
        Button(self.ContentFrame, text="Clear Drawing", font=self.App.adjust_font(11, bold=True), width=16,
               bg=t["accent"], fg="white", activebackground=t["accent_hover"], activeforeground="white",
               relief=FLAT, bd=0, pady=6, cursor="hand2",
               command=self.Editor.ClearDrawing).pack(pady=(10, 5))

        # Mouse on the image canvas draws
        self.canvas.bind("<ButtonPress-1>", self.OnPress)
        self.canvas.bind("<B1-Motion>", self.OnDrag)
        self.canvas.bind("<ButtonRelease-1>", self.OnRelease)
        self.canvas.config(cursor="crosshair")

        # update the preview when the zoom changes
        doc = self.Editor.active_image
        if doc is not None:
            self.zoom_trace = doc.zoom.trace_add("write", lambda *args: self.UpdatePreview())

        # Clean up the canvas when this panel is closed
        self.bind("<Destroy>", self.OnDestroy)

        self.HighlightColor()
        self.UpdatePreview()

    def SectionLabel(self, text):
        # thin line, then a small title (same look as the other panels)
        Frame(self.ContentFrame, bg=self.t["border"], height=1).pack(fill=X, padx=20, pady=(12, 0))
        label = Label(self.ContentFrame, text=text, font=self.App.adjust_font(11, bold=True),
                      bg=self.t["sidebar"], fg=self.t["text"])
        label.pack(anchor="w", padx=20, pady=(10, 0))

    # ---------------- Tool / Size / Color ----------------

    def BrushSize(self):
        # brush size in IMAGE pixels
        tool = self.tool.get()
        return max(1, int(round(self.SizeSlider.get() * TOOLS[tool]["size_mul"])))

    def DisplayZoom(self):
        # how big 1 image pixel is on screen (displayed size / real size)
        doc = self.Editor.active_image
        if doc is None or self.Editor.display_width == 0:
            return 1.0
        return self.Editor.display_width / doc.image.shape[1]

    def ScreenBrushSize(self):
        # brush size as it looks on the canvas
        return max(1, self.BrushSize() * self.DisplayZoom())

    def PreviewStyle(self):
        # how the stroke looks on the canvas while drawing (before it is applied)
        tool = self.tool.get()
        if tool == "Eraser":
            return "#ffffff", "gray50"
        if tool == "Highlighter":
            return self.color, "gray50"     # stipple = see-through look
        if tool == "Pencil":
            return self.color, "gray75"
        return self.color, ""

    def UpdatePreview(self):
        # draw the brush at its ON-SCREEN size, and never bigger than the box
        self.Preview.delete("all")

        size = self.ScreenBrushSize()
        too_big = size > MAX_PREVIEW_SIZE
        width = min(size, MAX_PREVIEW_SIZE)

        mid_y = PREVIEW_HEIGHT / 2
        color, stipple = self.PreviewStyle()

        if self.tool.get() == "Eraser":
            r = width / 2
            x = PREVIEW_WIDTH / 2
            self.Preview.create_oval(x - r, mid_y - r, x + r, mid_y + r, outline="gray", dash=(3, 3))
        else:
            # keep the round ends of the line inside the box
            left = 15 + width / 2
            right = PREVIEW_WIDTH - 15 - width / 2
            self.Preview.create_line(left, mid_y, right, mid_y, width=width, fill=color,
                                     capstyle=ROUND, stipple=stipple)

        if too_big:
            self.PreviewNote.config(text="Brush is bigger than this preview")
        else:
            self.PreviewNote.config(text="")

    def SetColor(self, color):
        self.color = color
        self.HighlightColor()
        self.UpdatePreview()

    def PickCustomColor(self):
        result = colorchooser.askcolor(color=self.color, title="Pick a color")
        if result and result[1]:
            self.SetColor(result[1])

    def HighlightColor(self):
        for color, swatch in self.swatches.items():
            border = THEME if color == self.color else self.normal_color
            swatch.config(highlightbackground=border, highlightcolor=border)

    def HexToBGR(self, hex_color):
        # "#rrggbb" -> (b, g, r) for OpenCV
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return (b, g, r)

    # ---------------- Drawing with the mouse ----------------

    def MousePosition(self, event):
        # canvas position (for the preview) and image position (for the real stroke)
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        zoom = self.DisplayZoom()
        ix = int((cx - self.Editor.image_x) / zoom)
        iy = int((cy - self.Editor.image_y) / zoom)
        return (cx, cy), (ix, iy), zoom

    def OnPress(self, event):
        if self.Editor.active_image is None:
            return
        self.points = []
        self.last_point = None
        self.OnDrag(event)

    def OnDrag(self, event):
        if self.Editor.active_image is None:
            return

        (cx, cy), image_point, zoom = self.MousePosition(event)
        self.points.append(image_point)

        # quick preview on the canvas, scaled by zoom so it matches the final stroke
        width = self.ScreenBrushSize()
        color, stipple = self.PreviewStyle()

        if self.last_point is None:
            r = width / 2
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="",
                                    stipple=stipple, tags="stroke_preview")
        else:
            lx, ly = self.last_point
            self.canvas.create_line(lx, ly, cx, cy, width=width, fill=color,
                                    capstyle=ROUND, joinstyle=ROUND, stipple=stipple,
                                    tags="stroke_preview")

        self.last_point = (cx, cy)

    def OnRelease(self, event):
        if not self.points:
            return

        tool = self.tool.get()
        self.Editor.AddStroke(self.points, self.HexToBGR(self.color), self.BrushSize(),
                              TOOLS[tool]["opacity"], erase=(tool == "Eraser"))

        self.canvas.delete("stroke_preview")
        self.points = []
        self.last_point = None

    # ---------------- Closing the panel ----------------

    def OnDestroy(self, event):
        if event.widget is not self:
            return

        # stop listening to zoom changes
        doc = self.Editor.active_image
        if doc is not None and self.zoom_trace is not None:
            try:
                doc.zoom.trace_remove("write", self.zoom_trace)
            except TclError:
                pass

        # When the whole app is closing, the canvas may already be destroyed
        try:
            if self.canvas.winfo_exists():
                self.canvas.delete("stroke_preview")
                self.canvas.unbind("<ButtonPress-1>")
                self.canvas.unbind("<B1-Motion>")
                self.canvas.unbind("<ButtonRelease-1>")
                self.canvas.config(cursor="")
        except TclError:
            pass