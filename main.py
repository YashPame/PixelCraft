from tkinter import *
from tkinter import ttk

from Components.top_header import Header
from Components.ribbon import Ribbon

from Core.image_editor import Editor

DEFAULT_WIDTH = 1536
DEFAULT_HEIGHT = 864

class PhotoEditorApp:
    def __init__(self, root):
        self.root = root
        self.ratioW, self.ratioH = self.setRatio()
        self.root.geometry(f'{str(int(DEFAULT_WIDTH*self.ratioW))}x{str(int(DEFAULT_HEIGHT*self.ratioH))}+0+0')
        self.root.config(bd=7, relief=SOLID)
        self.root.attributes('-fullscreen', True)

        self.Header = Header(self)
        self.place_component(self.Header, 1, 1, 1520, 45)

        self.canvas_frame = Frame(self.root)
        self.place_component(self.canvas_frame, 1,250, 1000, 500)

        self.canvas = Canvas(self.canvas_frame)
        # self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.grid(row=0,column=0,sticky="nsew")

        self.y_scrollbar = Scrollbar(
            self.canvas_frame,
            orient="vertical",
            command=self.canvas.yview
        )
        # self.y_scrollbar.pack(side="right", fill="y")
        self.y_scrollbar.grid(row=0,column=1,sticky="ns")

        self.x_scrollbar = Scrollbar(
            self.canvas_frame,
            orient="horizontal",
            command=self.canvas.xview
        )
        # self.x_scrollbar.pack(side="bottom", fill="x")
        self.x_scrollbar.grid(row=1,column=0,sticky="ew")

        self.canvas.configure(
            xscrollcommand=self.x_scrollbar.set,
            yscrollcommand=self.y_scrollbar.set
        )

        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)


        self.editor = Editor(self.canvas)
        
        self.Ribbon = Ribbon(self)
        self.place_component(self.Ribbon, 1, 50, 1520, 180)

        





    def setRatio(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        ratioW = DEFAULT_WIDTH / screen_width
        ratioH = DEFAULT_HEIGHT / screen_height
        return ratioW, ratioH
    
    def place_component(self, widget, x, y, w, h, **kwargs):
        widget.place(x=int(x*self.ratioW), y=int(y*self.ratioH), w=int(w*self.ratioW), h=int(h*self.ratioH), **kwargs)

    def scale_x(self, x):
        return int(x*self.ratioW)

    def scale_y(self, y):
            return int(y*self.ratioH)
    
    def adjust_font(self, font, font_name="times", bold=False):
        fontstr = f"{font_name} {int(font*self.ratioH)}"
        if bold:
            fontstr+=" bold"
        return fontstr
    
    
        
    
if __name__ == '__main__':
    root = Tk()
    obj = PhotoEditorApp(root)
    # root.overrideredirect(1)
    root.mainloop()