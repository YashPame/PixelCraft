from tkinter import *

class BaseComponent(Frame):
    def __init__(self, App):
        super().__init__(App.root)
        self.App = App

    def place_component(self, widget, x, y, w, h, **kwargs):
        widget.place(x=x, y=y, w=int(w*self.App.ratioW), h=int(h*self.App.ratioH), **kwargs)

    def adjust_font(self, font, font_name="times", bold=False):
        fontstr = f"{font_name} {int(font*self.App.ratioH)}"
        if bold:
            fontstr+=" bold"
        return fontstr
