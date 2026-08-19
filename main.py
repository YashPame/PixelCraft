from tkinter import *
from Components.top_header import Header
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
        self.Header.place_component(self.Header, 1, 1, 1520, 60)

    def setRatio(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        ratioW = DEFAULT_WIDTH / screen_width
        ratioH = DEFAULT_HEIGHT / screen_height
        return ratioW, ratioH
        
    
if __name__ == '__main__':
    root = Tk()
    obj = PhotoEditorApp(root)
    # root.overrideredirect(1)
    root.mainloop()