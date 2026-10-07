from tkinter import *
from PIL import Image, ImageTk
from tkinter import filedialog

class BackgroundRemover(Frame):
    def __init__(self, App, PanelFrame):
        super().__init__(PanelFrame)
        self.App = App

        self.config(bg="#2f3775")

    