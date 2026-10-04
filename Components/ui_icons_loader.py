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

        self.App.IconImage_OpenFile = LoadIcon("open_file.png", 30)

        self.App.IconImage_AIFeatures = LoadIcon("ai_features.png", 30)
        self.App.IconImage_Brightenss = LoadIcon("brightness.png", 30)
        self.App.IconImage_Brush = LoadIcon("brush.png", 30)
        self.App.IconImage_Crop = LoadIcon("crop.png", 30)
        self.App.IconImage_Eraser = LoadIcon("eraser.png", 30)
        self.App.IconImage_Pencil = LoadIcon("pencil.png", 30)

        self.App.IconImage_Undo = LoadIcon("undo.png", 20)
        self.App.IconImage_Redo = LoadIcon("redo.png", 20)
        self.App.IconImage_ZoomIn = LoadIcon("zoom_in.png", 20)
        self.App.IconImage_ZoomOut = LoadIcon("zoom_out.png", 20)