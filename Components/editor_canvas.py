from tkinter import *
from Core.image_editor import Editor


class EditorCanvas(Frame):
    def __init__(self, App):
        super().__init__(App.root)

        self.App = App

        self.canvas = Canvas(self)
        self.canvas.grid(row=0,column=0,sticky="nsew")

        self.y_scrollbar = Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )
        self.y_scrollbar.grid(row=0,column=1,sticky="ns")

        self.x_scrollbar = Scrollbar(
            self,
            orient="horizontal",
            command=self.canvas.xview
        )
        self.x_scrollbar.grid(row=1,column=0,sticky="ew")

        self.canvas.configure(
            xscrollcommand=self.x_scrollbar.set,
            yscrollcommand=self.y_scrollbar.set
        )

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)


        self.App.editor = Editor(self.canvas)
    
