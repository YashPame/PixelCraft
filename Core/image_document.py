from PIL import Image
import os
import cv2

class ImageDocument:
    def __init__(self, file_path):

        self.file_path = file_path
        self.file_name = os.path.basename(file_path)

        self.orignal_image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)

        self.image = self.orignal_image.copy()

        self.undo_stack = []
        self.redo_stack = []

        self.zoom = 1.0

        self.modified = False
        