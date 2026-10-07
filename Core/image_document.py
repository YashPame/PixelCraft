import os
import cv2
from tkinter import DoubleVar, StringVar


class ImageDocument:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.orignal_image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)

        self.undo_stack = []
        self.redo_stack = []

        self.zoom = DoubleVar(value=1.0)
        self.zoom_percentage = StringVar(value="100.0%")

        self.ResetEdits()

    def ResetEdits(self):
        # back to the original photo (used when opening and by Reset)
        self.image = self.orignal_image.copy()             # what is shown (everything applied)
        self.base_image = self.orignal_image.copy()        # after rotate / flip / crop / straighten
        self.processed_image = self.orignal_image.copy()   # base + adjustments + filter (no drawing)

        self.adjustments = {}
        self.filter_name = "Original"

        self.straighten_source = None   # base image before straightening
        self.straighten_angle = 0

        self.drawing_layer = None       # transparent BGRA layer with pen strokes (same size as base_image)
        self.drawing_source = None      # drawing layer before straightening

        self.modified = False