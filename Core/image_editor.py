import cv2

from tkinter import filedialog
from PIL import Image, ImageTk

from Core.image_document import ImageDocument
from tkinter import messagebox

class Editor:
    def __init__(self, canvas):
        self.canvas = canvas
        self.images = []
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

        self.images.append(image)
        self.active_image=image

        self.ShowImage()

        return image

    def ShowImage(self):
        if self.active_image is None:
            return

        image = self.active_image.image

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        if self.active_image.zoom != 1.0:
            width = int(pil_image.width*self.active_image.zoom)
            height = int(pil_image.height*self.active_image.zoom)
            pil_image = pil_image.resize((width, height))

        photo = ImageTk.PhotoImage(pil_image)

        self.active_image.photo_image = photo

        self.canvas.delete("all")

        self.canvas_image_id = self.canvas.create_image(
            0,0,anchor="nw",image=photo
        )

        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )

        self.canvas.update_idletasks()

        print("Image displayed")