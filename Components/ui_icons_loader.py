from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk


class UIIconsLoader():
    def __init__(self, App):
        self.App = App

        self.App.IconImage_OpenFile = ImageTk.PhotoImage(Image.open("Icons/open_file.png").resize((30, 30), Image.Resampling.LANCZOS))
        
        self.App.IconImage_AIFeatures = ImageTk.PhotoImage(Image.open("Icons/ai_features.png").resize((30, 30), Image.Resampling.LANCZOS))
        self.App.IconImage_Brightenss = ImageTk.PhotoImage(Image.open("Icons/brightness.png").resize((30, 30), Image.Resampling.LANCZOS))
        self.App.IconImage_Brush = ImageTk.PhotoImage(Image.open("Icons/brush.png").resize((30, 30), Image.Resampling.LANCZOS))
        self.App.IconImage_Crop = ImageTk.PhotoImage(Image.open("Icons/crop.png").resize((30, 30), Image.Resampling.LANCZOS))
        self.App.IconImage_Eraser = ImageTk.PhotoImage(Image.open("Icons/eraser.png").resize((30, 30), Image.Resampling.LANCZOS))
        self.App.IconImage_Pencil = ImageTk.PhotoImage(Image.open("Icons/pencil.png").resize((30, 30), Image.Resampling.LANCZOS))

        self.App.IconImage_Undo = ImageTk.PhotoImage(Image.open("Icons/undo.png").resize((20, 20), Image.Resampling.LANCZOS))
        self.App.IconImage_Redo = ImageTk.PhotoImage(Image.open("Icons/redo.png").resize((20, 20), Image.Resampling.LANCZOS))
        self.App.IconImage_ZoomIn = ImageTk.PhotoImage(Image.open("Icons/zoom_in.png").resize((20, 20), Image.Resampling.LANCZOS))
        self.App.IconImage_ZoomOut = ImageTk.PhotoImage(Image.open("Icons/zoom_out.png").resize((20, 20), Image.Resampling.LANCZOS))
