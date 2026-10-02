from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk


class Variables():
    def __init__(self, App):
        self.App = App

        self.App.hasImage = BooleanVar()
        self.App.hasImage.set(False)

        self.App.activeTopButton = StringVar()
        self.App.activeTopButton.set("None")
        
