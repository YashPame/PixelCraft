import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk


class ImageDocument:
    def __init__(self, file_path):
        self.file_path = file_path

        # Original image — never modify this
        self.original = Image.open(file_path).convert("RGBA")

        # Working image — all edits happen to this
        self.image = self.original.copy()

        # Reference to Tkinter's displayed image
        self.photo_image = None


class PhotoEditor:
    def __init__(self, root):
        self.root = root

        self.canvas = tk.Canvas(root, bg="gray")
        self.canvas.pack(fill="both", expand=True)

        # All currently opened images
        self.documents = []

        # Currently active document
        self.active_document = None

    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("All Files", "*.*")
            ]
        )

        if not file_path:
            return

        # Create a document for this image
        document = ImageDocument(file_path)

        # Store it
        self.documents.append(document)

        # Make it the active image
        self.active_document = document

        # Display it
        self.display_image()

    def display_image(self):
        if self.active_document is None:
            return

        image = self.active_document.image

        # Convert PIL Image -> Tkinter PhotoImage
        self.active_document.photo_image = ImageTk.PhotoImage(image)

        # Clear canvas
        self.canvas.delete("all")

        # Put image on canvas
        self.canvas.create_image(
            0,
            0,
            anchor="nw",
            image=self.active_document.photo_image
        )

        # Make canvas fit image
        self.canvas.config(
            scrollregion=self.canvas.bbox("all")
        )


root = tk.Tk()
root.geometry("1000x700")

editor = PhotoEditor(root)

root.mainloop()