from tkinter import * 
from PIL import Image, ImageTk 
from tkinter import filedialog 
 
class LightPanel(Frame): 
    def __init__(self, App, PanelFrame): 
        super().__init__(PanelFrame) 
        self.App = App 
 
        self.LightColorOptionsInstances = {} 
 
        self.Canvas = Canvas(self, highlightthickness=0) 
        self.ScrollableFrame = Frame(self.Canvas) 
 
        self.ScrollableFrame.bind("<Configure>", lambda e: self.Canvas.configure(scrollregion=self.Canvas.bbox("all"))) 
        self.Canvas.create_window((0, 0), window=self.ScrollableFrame, anchor="nw") 
 
        self.Canvas.pack(side=LEFT, fill=BOTH, expand=True) 
 
        LightLabel = Label(self.ScrollableFrame, text="Light", font=("Arial", 16), fg="#2f3775") 
        LightLabel.pack(pady=5) 
 
        LightOptions = ["Brightness", "Exposure", "Contrast", "Highlights", "Shadows", "Vignette"] 
 
        for option in LightOptions: 
            optionFrame = Frame(self.ScrollableFrame) 
            optionFrame.pack(pady=5) 
 
            optionLabel = Label(optionFrame, text=option, font=("Arial", 12), fg="#2f3775", width=12, anchor="w") 
            optionLabel.grid(row=0, column=0, padx=25, pady=(15, 0), sticky="w") 
 
            optionSlider = Scale(optionFrame, from_=-100, to=100, orient=HORIZONTAL, length=200) 
            optionSlider.set(0) 
            optionSlider.grid(row=0, column=1, padx=5) 
            optionSlider.bind("<ButtonRelease-1>", self.UpdateValues) 
 
            self.LightColorOptionsInstances[option] = optionSlider 
 
        ColorOptions = ["Saturation", "Warmth", "Tint", "Sharpness"] 
 
        ColorLabel = Label(self.ScrollableFrame, text="Color", font=("Arial", 16), fg="#2f3775") 
        ColorLabel.pack(pady=5) 
        
        for option in ColorOptions: 
            optionFrame = Frame(self.ScrollableFrame) 
            optionFrame.pack(pady=5) 
 
            optionLabel = Label(optionFrame, text=option, font=("Arial", 12), fg="#2f3775", width=12, anchor="w") 
            optionLabel.grid(row=0, column=0, padx=25, pady=(15, 0), sticky="w") 
 
            optionSlider = Scale(optionFrame, from_=-100, to=100, orient=HORIZONTAL, length=200) 
            optionSlider.set(0) 
            optionSlider.grid(row=0, column=1, padx=5) 
            optionSlider.bind("<ButtonRelease-1>", self.UpdateValues) 
 
            self.LightColorOptionsInstances[option] = optionSlider 
 
        self.Canvas.bind_all("<MouseWheel>", self.Scroll) 
 
    def UpdateValues(self, event): 
        Values = {} 
 
        for option, slider in self.LightColorOptionsInstances.items(): 
            Values[option] = slider.get() 
 
        print(Values) 
 
    def Scroll(self, event): 
        self.Canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")