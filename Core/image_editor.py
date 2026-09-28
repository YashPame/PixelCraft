import cv2
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk

from Core.image_document import ImageDocument
from tkinter import messagebox

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
        self.App.hasImage.set(True)

        self.ShowImage()

        return image

    def ShowImage(self):
        if self.active_image is None:
            return

        image = self.active_image.image

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        if self.active_image.zoom != 1.0:
            width = int(pil_image.width * self.active_image.zoom)
            height = int(pil_image.height * self.active_image.zoom)
            pil_image = pil_image.resize((width, height))

        photo = ImageTk.PhotoImage(pil_image)

        self.active_image.photo_image = photo

        self.canvas.delete("all")

        # Make sure Tkinter has calculated the actual canvas size
        self.canvas.update_idletasks()

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        image_width = pil_image.width
        image_height = pil_image.height

        # Center small images
        x = max((canvas_width - image_width) // 2, 0)
        y = max((canvas_height - image_height) // 2, 0)

        self.canvas_image_id = self.canvas.create_image(
            x,
            y,
            anchor="nw",
            image=photo
        )

        # Calculate scrollable area
        scroll_width = max(canvas_width, x + image_width)
        scroll_height = max(canvas_height, y + image_height)

        self.canvas.configure(
            scrollregion=(0, 0, scroll_width, scroll_height)
        )

        self.canvas.update_idletasks()

        print("Image displayed")