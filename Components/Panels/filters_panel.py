from tkinter import *
import cv2
from PIL import Image, ImageTk

FILTERS = ["Original", "Grayscale", "Sepia",
           "Vintage", "Noir", "Vivid",
           "Warm", "Cool", "Fade",
           "Invert", "Sketch", "Emboss"]

PREVIEW_SIZE = 100       # preview box size in pixels
COLUMNS = 3
SELECTED_COLOR = "#2f3775"

class FiltersPanel(Frame):
    def __init__(self, App, PanelFrame):
        super().__init__(PanelFrame)
        self.App = App
        self.Editor = App.editor

        self.cells = {}      # filter name -> (cell frame, image label)
        self.photos = {}     # keep PhotoImages alive (Tkinter deletes them otherwise)

        self.ContentFrame = Frame(self)
        self.ContentFrame.pack(fill=BOTH, expand=True)

        title = Label(self.ContentFrame, text="Filters", font=("Arial", 16), fg=SELECTED_COLOR)
        title.pack(pady=10)

        grid = Frame(self.ContentFrame)
        grid.pack()

        self.normal_color = self.cget("bg")   # panel background, used for unselected border

        for index, name in enumerate(FILTERS):
            row, col = divmod(index, COLUMNS)

            # the border (highlight) of this frame shows which filter is selected
            cell = Frame(grid, highlightthickness=3, highlightbackground=self.normal_color, cursor="hand2")
            cell.grid(row=row, column=col, padx=8, pady=6)

            image_label = Label(cell, width=PREVIEW_SIZE, height=PREVIEW_SIZE, bg="#dddddd")
            image_label.pack()

            name_label = Label(cell, text=name, font=("Arial", 10), fg=SELECTED_COLOR)
            name_label.pack(pady=(2, 0))

            # clicking anywhere on the cell applies the filter
            for widget in (cell, image_label, name_label):
                widget.bind("<Button-1>", lambda e, n=name: self.FilterClicked(n))

            self.cells[name] = (cell, image_label)

        # Let the Editor find this panel (to refresh after Undo / Redo / Reset)
        self.App.filters_panel = self
        self.bind("<Destroy>", self.OnDestroy)

        self.Refresh()

    def FilterClicked(self, name):
        self.Editor.SetFilter(name)
        self.Highlight()

    def Refresh(self):
        # Make the previews again and show which filter is selected
        self.MakePreviews()
        self.Highlight()

    def MakePreviews(self):
        doc = self.Editor.active_image
        if doc is None:
            return

        # small copy of the image so 12 previews are fast
        base = doc.base_image
        h, w = base.shape[:2]
        scale = PREVIEW_SIZE / max(h, w)
        small = cv2.resize(base, (max(1, int(w * scale)), max(1, int(h * scale))),
                           interpolation=cv2.INTER_AREA)

        for name, (cell, image_label) in self.cells.items():
            # same processing as the real image: adjustments + this filter
            preview = self.Editor.ProcessImage(small, doc.adjustments, name)
            photo = self.ToPhoto(preview)
            self.photos[name] = photo
            image_label.config(image=photo)

    def Highlight(self):
        doc = self.Editor.active_image
        selected = doc.filter_name if doc is not None else "Original"

        for name, (cell, image_label) in self.cells.items():
            color = SELECTED_COLOR if name == selected else self.normal_color
            cell.config(highlightbackground=color, highlightcolor=color)

    def ToPhoto(self, cv_img):
        # OpenCV image -> Tkinter PhotoImage
        if cv_img.ndim == 2:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        elif cv_img.shape[2] == 4:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
        else:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        return ImageTk.PhotoImage(Image.fromarray(rgb))

    def OnDestroy(self, event):
        if event.widget is not self:
            return
        if getattr(self.App, "filters_panel", None) is self:
            self.App.filters_panel = None