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
        self.image = self.orignal_image.copy()             
        self.base_image = self.orignal_image.copy()       
        self.processed_image = self.orignal_image.copy()   

        self.adjustments = {}
        self.filter_name = "Original"

        self.straighten_source = None   
        self.straighten_angle = 0

        self.drawing_layer = None       
        self.drawing_source = None      

        self.modified = False