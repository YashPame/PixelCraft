from PIL import Image
import os
import cv2
from tkinter import DoubleVar, StringVar

CANVAS_WIDTH = 620
CANVAS_HEIGHT = 620
MAX_HISTORY = 20

class ImageDocument:
    def __init__(self, file_path):

        self.file_path = file_path
        self.file_name = os.path.basename(file_path)

        self.orignal_image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)

        self.image = self.orignal_image.copy()        # what is shown (everything applied)
        self.base_image = self.orignal_image.copy()   # after rotate / flip / crop

        self.undo_stack = []
        self.redo_stack = []

        self.zoom = DoubleVar()
        self.zoom.set(1.0)
        self.zoom_percentage = StringVar()
        self.zoom_percentage.set("100.0%")

        self.modified = False
        self.adjustments = {}

        self.straighten_source = None
        self.straighten_angle = 0

        self.filter_name = "Original"

        # NEW: drawing
        self.processed_image = self.orignal_image.copy()   # base + adjustments + filter (no drawing)
        self.drawing_layer = None    # transparent BGRA layer with pen strokes (same size as base_image)
        self.drawing_source = None   # drawing layer before straightening