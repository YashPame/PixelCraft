import os
import sys
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk


def resource_path(relative_path):
    # When running as an .exe, PyInstaller unpacks files to a temp folder (sys._MEIPASS).
    # When running normally, use the project folder.
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def LoadIcon(file_name, size):
    path = resource_path(os.path.join("Icons", file_name))
    image = Image.open(path).resize((size, size), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)


class UIIconsLoader():
    def __init__(self, App):
        self.App = App
        # icons grow / shrink with the screen, like the buttons they sit in
        self.scale = min(App.ratioW, App.ratioH)

        self.App.IconImage_OpenFile = self.Icon("open_file.png", 30)

        self.App.IconImage_BackgroundRemover = self.Icon("background_remover.png", 30)
        self.App.IconImage_Brightenss = self.Icon("brightness.png", 30)
        self.App.IconImage_Brush = self.Icon("brush.png", 30)
        self.App.IconImage_Crop = self.Icon("crop.png", 30)
        self.App.IconImage_Eraser = self.Icon("eraser.png", 30)
        self.App.IconImage_Pencil = self.Icon("pencil.png", 30)

        self.App.IconImage_Undo = self.Icon("undo.png", 20)
        self.App.IconImage_Redo = self.Icon("redo.png", 20)
        self.App.IconImage_ZoomIn = self.Icon("zoom_in.png", 20)
        self.App.IconImage_ZoomOut = self.Icon("zoom_out.png", 20)

        self.App.IconImage_RotateLeft = self.Icon("rotate_left.png", 30)
        self.App.IconImage_RotateRight = self.Icon("rotate_right.png", 30)
        self.App.IconImage_FlipHorizontal = self.Icon("horizontal_flip.png", 30)
        self.App.IconImage_FlipVertical = self.Icon("vertical_flip.png", 30)

    def Icon(self, file_name, size):
        # size is for the 1536 x 864 design screen
        return LoadIcon(file_name, max(12, round(size * self.scale)))