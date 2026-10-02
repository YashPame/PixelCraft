from tkinter import *
from PIL import Image, ImageTk
from tkinter import filedialog

class FiltersPanel(Frame):
    def __init__(self, App, PanelFrame):
        super().__init__(PanelFrame)
        self.App = App
       