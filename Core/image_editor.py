import cv2
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk

from Core.image_document import ImageDocument
from tkinter import messagebox

CANVAS_WIDTH = 620
CANVAS_HEIGHT = 620
MAX_HISTORY = 20
MAX_ZOOM = 10.0
MIN_ZOOM = 0.20
ZOOM_STEP = 0.05

class Editor:
    def __init__(self, App, canvas):
        self.canvas = canvas
        self.App = App
        self.active_image = None
        self.canvas_image_id = None


    def OpenImage(self):
        file_path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
        )

        if not file_path:
            return None

        try:
            image = ImageDocument(file_path)
        except:
            messagebox.showerror("Error", "Something Went Wrong, Unable to open File...")

        self.active_image=image
        self.SetInitialZoom()
        self.App.hasImage.set(True)

        self.ShowImage()

        return image

    def ShowImage(self):
        if self.active_image is None:
            return

        image = self.active_image.image
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        image_width = pil_image.width
        image_height = pil_image.height

        zoom = self.active_image.zoom.get()

        if zoom != 1.0:
            width = int(image_width * zoom)
            height = int(image_height * zoom)
            pil_image = pil_image.resize((width, height))

        photo = ImageTk.PhotoImage(pil_image)
        self.active_image.photo_image = photo
        self.canvas.delete("all")
        self.canvas.update_idletasks()

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width = pil_image.width
        image_height = pil_image.height

        x = max((canvas_width - image_width) // 2, 0)
        y = max((canvas_height - image_height) // 2, 0)

        self.canvas_image_id = self.canvas.create_image(x, y, anchor="nw", image=photo)

        scroll_width = max(canvas_width, x + image_width)
        scroll_height = max(canvas_height, y + image_height)

        self.canvas.configure(scrollregion=(0, 0, scroll_width, scroll_height))
        print("Image displayed", self.active_image.file_name, "Zoom:", self.active_image.zoom.get())

    def SetInitialZoom(self):
        image = self.active_image.image

        image_height, image_width = image.shape[:2]

        if image_width > CANVAS_WIDTH or image_height > CANVAS_HEIGHT:
            width_ratio = CANVAS_WIDTH / image_width
            height_ratio = CANVAS_HEIGHT / image_height
            zoom = min(width_ratio, height_ratio)
        else:
            zoom = 1.0

        self.active_image.initial_zoom = zoom
        self.active_image.zoom.set(zoom)
        self.active_image.zoom_percentage.set(f"{round(self.active_image.zoom.get() * 100, 2)}%")

    def GetState(self):
        return {
            "image": self.active_image.image.copy(),
            "zoom": self.active_image.zoom.get()
        }

    def SaveState(self):
        state = self.GetState()

        self.active_image.undo_stack.append(state)

        if len(self.active_image.undo_stack) > MAX_HISTORY:
            self.active_image.undo_stack.pop(0)

        self.active_image.redo_stack.clear()

    def ZoomIn(self):
        if self.active_image is None:
            return
        zoom = self.active_image.zoom.get()
        if zoom >= MAX_ZOOM:
            return
        self.SaveState()
        zoom = min(zoom + ZOOM_STEP, MAX_ZOOM)
        self.active_image.zoom.set(zoom)
        self.active_image.zoom_percentage.set(f"{round(zoom * 100, 2)}%")
        self.ShowImage()

    def ZoomOut(self):
        if self.active_image is None:
            return
        zoom = self.active_image.zoom.get()
        if zoom <= MIN_ZOOM:
            return
        self.SaveState()
        zoom = max(zoom - ZOOM_STEP, MIN_ZOOM)
        self.active_image.zoom.set(zoom)
        self.active_image.zoom_percentage.set(f"{round(zoom * 100, 2)}%")
        self.ShowImage()

    def Undo(self):
        if self.active_image is None:
            return

        if not self.active_image.undo_stack:
            return

        self.active_image.redo_stack.append(self.GetState())

        state = self.active_image.undo_stack.pop()

        self.active_image.image = state["image"]
        self.active_image.zoom.set(state["zoom"])
        self.active_image.zoom_percentage.set(f"{round(self.active_image.zoom.get() * 100, 2)}%")

        self.ShowImage()

    def Redo(self):
        if self.active_image is None:
            return

        if not self.active_image.redo_stack:
            return

        self.active_image.undo_stack.append(self.GetState())

        state = self.active_image.redo_stack.pop()

        self.active_image.image = state["image"]
        self.active_image.zoom.set(state["zoom"])
        self.active_image.zoom_percentage.set(f"{round(self.active_image.zoom.get() * 100, 2)}%")

        self.ShowImage()

    def Reset(self):
        if self.active_image is None:
            return

        self.SaveState()

        self.active_image.image = self.active_image.orignal_image.copy()
        self.active_image.zoom.set(self.active_image.initial_zoom)
        self.active_image.zoom_percentage.set(f"{round(self.active_image.zoom.get() * 100, 2)}%")

        self.active_image.modified = False

        self.active_image.undo_stack.clear()
        self.active_image.redo_stack.clear()

        self.ShowImage()

    def LightAdjustment(self, parameter, value):
        pass
    