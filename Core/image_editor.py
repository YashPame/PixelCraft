import cv2
import math
import numpy as np
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageEnhance, ImageFilter, ImageTk
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageTk

from Core.image_document import ImageDocument

# Order in which adjustments are applied (always the same, whatever the slider order)
ADJUSTMENT_ORDER = ["Exposure", "Brightness", "Contrast", "Highlights", "Shadows",
                    "Saturation", "Warmth", "Tint", "Sharpness", "Vignette"]

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
        self.state_before_adjust = None

        # NEW: where the image is drawn on the canvas (used by the crop box)
        self.image_x = 0
        self.image_y = 0
        self.display_width = 0
        self.display_height = 0

    # ---------------- Open / Show ----------------

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
            return None

        self.active_image = image
        self.SetInitialZoom()
        self.App.hasImage.set(True)
        self.SyncSliders()

        self.ShowImage()

        return image

    def ShowImage(self):
        if self.active_image is None:
            return

        image = self.active_image.image

        if image.ndim == 2:                          # grayscale image
            rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:                    # transparent PNG
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
        else:                                        # normal image
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        pil_image = Image.fromarray(rgb_image)

        zoom = self.active_image.zoom.get()

        if zoom != 1.0:
            width = int(pil_image.width * zoom)
            height = int(pil_image.height * zoom)
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

        # NEW: remember where the image is on the canvas
        self.image_x = x
        self.image_y = y
        self.display_width = image_width
        self.display_height = image_height

        scroll_width = max(canvas_width, x + image_width)
        scroll_height = max(canvas_height, y + image_height)

        self.canvas.configure(scrollregion=(0, 0, scroll_width, scroll_height))

        # NEW: if the crop panel is open, draw the crop box again on top of the image
        crop_panel = getattr(self.App, "crop_panel", None)
        if crop_panel is not None and crop_panel.winfo_exists():
            crop_panel.DrawCropBox()

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

    # ---------------- Undo / Redo ----------------

    def GetState(self):
        source = self.active_image.straighten_source
        return {
            "image": self.active_image.image.copy(),
            "base_image": self.active_image.base_image.copy(),
            "zoom": self.active_image.zoom.get(),
            "adjustments": dict(self.active_image.adjustments),
            "straighten_source": None if source is None else source.copy(),
            "straighten_angle": self.active_image.straighten_angle,
            "filter_name": self.active_image.filter_name        # NEW
        }

    def RestoreState(self, state):
        # NEW: used by Undo and Redo
        doc = self.active_image
        doc.image = state["image"]
        doc.base_image = state["base_image"]
        doc.zoom.set(state["zoom"])
        doc.zoom_percentage.set(f"{round(doc.zoom.get() * 100, 2)}%")
        doc.adjustments = state["adjustments"]
        doc.straighten_source = state["straighten_source"]
        doc.straighten_angle = state["straighten_angle"]
        doc.filter_name = state["filter_name"] 

        self.SyncSliders()
        self.ShowImage()

    def SaveState(self):
        state = self.GetState()

        self.active_image.undo_stack.append(state)

        if len(self.active_image.undo_stack) > MAX_HISTORY:
            self.active_image.undo_stack.pop(0)

        self.active_image.redo_stack.clear()

    def Undo(self):
        if self.active_image is None or not self.active_image.undo_stack:
            return

        self.active_image.redo_stack.append(self.GetState())
        self.RestoreState(self.active_image.undo_stack.pop())

    def Redo(self):
        if self.active_image is None or not self.active_image.redo_stack:
            return

        self.active_image.undo_stack.append(self.GetState())
        self.RestoreState(self.active_image.redo_stack.pop())

    def StartAdjust(self):
        # remember how the image looked before a slider drag started
        if self.active_image is None:
            return
        self.state_before_adjust = self.GetState()

    def EndAdjust(self):
        # after the drag: add ONE undo entry, but only if something changed
        if self.active_image is None or self.state_before_adjust is None:
            return

        before = self.state_before_adjust
        doc = self.active_image

        changed = (before["adjustments"] != doc.adjustments or
                   before["straighten_angle"] != doc.straighten_angle)   # CHANGED

        if changed:
            doc.undo_stack.append(before)

            if len(doc.undo_stack) > MAX_HISTORY:
                doc.undo_stack.pop(0)

            doc.redo_stack.clear()

        self.state_before_adjust = None

    def SyncSliders(self):
        # Move the sliders in the open panel to match the current image
        if self.active_image is None:
            return

        light_panel = getattr(self.App, "light_panel", None)
        if light_panel is not None and light_panel.winfo_exists():
            light_panel.SetValues(self.active_image.adjustments)

        crop_panel = getattr(self.App, "crop_panel", None)          # NEW
        if crop_panel is not None and crop_panel.winfo_exists():
            crop_panel.SetAngle(self.active_image.straighten_angle)

        filters_panel = getattr(self.App, "filters_panel", None)     # NEW
        if filters_panel is not None and filters_panel.winfo_exists():
            filters_panel.Refresh()
    # ---------------- Zoom / Reset ----------------

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

    def Reset(self):
        if self.active_image is None:
            return

        doc = self.active_image
        doc.image = doc.orignal_image.copy()
        doc.base_image = doc.orignal_image.copy()
        doc.adjustments = {}
        doc.straighten_source = None      # NEW
        doc.straighten_angle = 0          # NEW
        doc.filter_name = "Original"
        doc.modified = False

        doc.undo_stack.clear()
        doc.redo_stack.clear()

        self.SetInitialZoom()   # CHANGED: re-fit, because crop may have changed the size
        self.SyncSliders()
        self.ShowImage()

    # ---------------- Rotate / Flip / Straighten / Crop (NEW) ----------------

    def Rotate90(self, clockwise=True):
        if self.active_image is None:
            return

        self.SaveState()

        if clockwise:
            code = cv2.ROTATE_90_CLOCKWISE
        else:
            code = cv2.ROTATE_90_COUNTERCLOCKWISE

        self.active_image.base_image = cv2.rotate(self.active_image.base_image, code)
        self.ClearStraighten()
        self.RenderImage()
        self.ShowImage()

    def Flip(self, horizontal=True):
        if self.active_image is None:
            return

        self.SaveState()

        # 1 = flip left/right, 0 = flip up/down
        flip_code = 1 if horizontal else 0
        self.active_image.base_image = cv2.flip(self.active_image.base_image, flip_code)
        self.ClearStraighten()
        self.RenderImage()
        self.ShowImage()

    def Straighten(self, angle):
        # Called while the slider moves. Always rotates from the image
        # before straightening, so 10° then 5° gives 5°, not 15°.
        if self.active_image is None:
            return

        doc = self.active_image

        if angle == doc.straighten_angle:
            return

        if doc.straighten_source is None:
            doc.straighten_source = doc.base_image.copy()

        doc.straighten_angle = angle
        doc.base_image = self.RotateAndFill(doc.straighten_source, angle)
        self.RenderImage()
        self.ShowImage()

    def RotateAndFill(self, img, angle):
        # Rotate by any angle and zoom in just enough so no empty corners show
        if angle == 0:
            return img.copy()

        h, w = img.shape[:2]
        a = math.radians(abs(angle))

        scale = max(math.cos(a) + (h / w) * math.sin(a),
                    math.cos(a) + (w / h) * math.sin(a))

        # OpenCV uses positive = anticlockwise, so -angle makes positive = clockwise
        matrix = cv2.getRotationMatrix2D((w / 2, h / 2), -angle, scale)
        return cv2.warpAffine(img, matrix, (w, h), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REPLICATE)

    def ClearStraighten(self):
        # After rotate/flip/crop the straighten angle becomes part of the image
        self.active_image.straighten_source = None
        self.active_image.straighten_angle = 0
        self.SyncSliders()

    def Crop(self, left, top, right, bottom):
        # left/top/right/bottom are fractions of the image (0 to 1)
        if self.active_image is None:
            return

        doc = self.active_image
        h, w = doc.base_image.shape[:2]

        x1, y1 = int(left * w), int(top * h)
        x2, y2 = int(right * w), int(bottom * h)

        if x2 - x1 < 2 or y2 - y1 < 2:
            return

        self.SaveState()

        doc.base_image = doc.base_image[y1:y2, x1:x2].copy()
        self.ClearStraighten()
        self.RenderImage()
        self.SetInitialZoom()   # fit the new (smaller) image in the canvas
        self.ShowImage()

    # ---------------- Light / Color adjustments ----------------

    def ApplyCurve(self, pil_img, func):
        # Build a lookup table (old value 0-255 -> new value) and apply it to every channel
        table = [int(min(255, max(0, func(x)))) for x in range(256)]
        return pil_img.point(table * len(pil_img.getbands()))

    def LightAdjustment(self, pil_img, parameter, value):
        # pil_img is an RGB PIL image, value is between -100 and 100
        factor = 1 + value / 100      # -100 -> 0.0, 0 -> 1.0 (no change), +100 -> 2.0

        if parameter == "Brightness":
            pil_img = ImageEnhance.Brightness(pil_img).enhance(factor)

        elif parameter == "Exposure":
            # gamma curve: brightens/darkens mid-tones without blowing out whites
            gamma = 2 ** (-value / 100)
            pil_img = self.ApplyCurve(pil_img, lambda x: 255 * (x / 255) ** gamma)

        elif parameter == "Contrast":
            pil_img = ImageEnhance.Contrast(pil_img).enhance(factor)

        elif parameter == "Highlights":
            # only changes bright values (above 128)
            pil_img = self.ApplyCurve(pil_img, lambda x: x + value * max(0, (x - 128) / 127))

        elif parameter == "Shadows":
            # only changes dark values (below 128)
            pil_img = self.ApplyCurve(pil_img, lambda x: x + value * max(0, (128 - x) / 128))

        elif parameter == "Saturation":
            # ImageEnhance.Color = saturation (0 = black & white)
            pil_img = ImageEnhance.Color(pil_img).enhance(factor)

        elif parameter == "Warmth":
            # more red + less blue = warmer
            r, g, b = pil_img.split()
            r = self.ApplyCurve(r, lambda x: x + value / 2)
            b = self.ApplyCurve(b, lambda x: x - value / 2)
            pil_img = Image.merge("RGB", (r, g, b))

        elif parameter == "Tint":
            # less green = magenta, more green = green
            r, g, b = pil_img.split()
            g = self.ApplyCurve(g, lambda x: x - value / 2)
            pil_img = Image.merge("RGB", (r, g, b))

        elif parameter == "Sharpness":
            # 0 = blurred, 1 = original, 2 = sharpened
            pil_img = ImageEnhance.Sharpness(pil_img).enhance(factor)

        elif parameter == "Vignette":
            strength = abs(value) / 100

            # radial_gradient: black in the center, white at the edges (256x256)
            mask = Image.radial_gradient("L").filter(ImageFilter.GaussianBlur(4))
            mask = mask.resize(pil_img.size)

            # keep the center clean, apply the effect mostly at the edges
            mask = mask.point(lambda x: int((x / 255) ** 2 * 255 * strength))

            # negative = dark edges, positive = white edges
            color = (0, 0, 0) if value < 0 else (255, 255, 255)
            edge_color = Image.new("RGB", pil_img.size, color)

            # where mask is white -> edge_color, where mask is black -> original image
            pil_img = Image.composite(edge_color, pil_img, mask)

        return pil_img

    def ApplyAdjustments(self, values, save_state=True):
        if self.active_image is None:
            return

        # Keep only sliders that are not 0
        values = {k: v for k, v in values.items() if v != 0}

        # Nothing changed -> do nothing
        if values == self.active_image.adjustments:
            return

        if save_state:
            self.SaveState()

        self.active_image.adjustments = values
        self.RenderImage()      # CHANGED: the work moved into RenderImage
        self.ShowImage()

    def RenderImage(self):
        # image = base_image + light/color adjustments + filter
        doc = self.active_image
        doc.image = self.ProcessImage(doc.base_image, doc.adjustments, doc.filter_name)
        doc.modified = True

    def ProcessImage(self, img, adjustments, filter_name):
        # Works on any size image: used for the real image AND the filter previews
        if not adjustments and filter_name == "Original":
            return img.copy()

        # Handle grayscale and transparent (PNG) images
        alpha = None
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            alpha = img[:, :, 3]
            img = img[:, :, :3]

        # OpenCV (BGR) -> PIL (RGB)
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        # 1. light / color sliders
        for parameter in ADJUSTMENT_ORDER:
            if parameter in adjustments:
                pil_img = self.LightAdjustment(pil_img, parameter, adjustments[parameter])

        # 2. filter
        pil_img = self.ApplyFilter(pil_img, filter_name)

        # PIL (RGB) -> OpenCV (BGR)
        result = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        if alpha is not None:
            result = np.dstack([result, alpha])

        return result



    def SetFilter(self, filter_name):
        # Called when a filter preview is clicked
        if self.active_image is None:
            return
        if filter_name == self.active_image.filter_name:
            return

        self.SaveState()
        self.active_image.filter_name = filter_name
        self.RenderImage()
        self.ShowImage()

    def ApplyFilter(self, pil_img, name):
        # pil_img is an RGB PIL image
        if name == "Grayscale":
            pil_img = ImageOps.grayscale(pil_img).convert("RGB")

        elif name == "Sepia":
            # gray image, then dark brown for shadows and cream for highlights
            gray = ImageOps.grayscale(pil_img)
            pil_img = ImageOps.colorize(gray, black="#2e1f0f", white="#f5e6c8")

        elif name == "Vintage":
            # half sepia mixed with the original, slightly faded
            gray = ImageOps.grayscale(pil_img)
            sepia = ImageOps.colorize(gray, black="#3b2a1a", white="#fff2d5")
            pil_img = Image.blend(pil_img, sepia, 0.5)
            pil_img = ImageEnhance.Contrast(pil_img).enhance(0.85)

        elif name == "Noir":
            # strong black & white
            gray = ImageOps.grayscale(pil_img)
            gray = ImageOps.autocontrast(gray, cutoff=2)
            pil_img = ImageEnhance.Contrast(gray).enhance(1.5).convert("RGB")

        elif name == "Vivid":
            pil_img = ImageEnhance.Color(pil_img).enhance(1.6)
            pil_img = ImageEnhance.Contrast(pil_img).enhance(1.15)

        elif name == "Warm":
            r, g, b = pil_img.split()
            r = self.ApplyCurve(r, lambda x: x + 25)
            b = self.ApplyCurve(b, lambda x: x - 25)
            pil_img = Image.merge("RGB", (r, g, b))

        elif name == "Cool":
            r, g, b = pil_img.split()
            r = self.ApplyCurve(r, lambda x: x - 20)
            b = self.ApplyCurve(b, lambda x: x + 25)
            pil_img = Image.merge("RGB", (r, g, b))

        elif name == "Fade":
            pil_img = ImageEnhance.Contrast(pil_img).enhance(0.75)
            pil_img = ImageEnhance.Brightness(pil_img).enhance(1.08)
            pil_img = ImageEnhance.Color(pil_img).enhance(0.8)

        elif name == "Invert":
            pil_img = ImageOps.invert(pil_img)

        elif name == "Sketch":
            # pencil-like outlines on white
            gray = ImageOps.grayscale(pil_img)
            pil_img = gray.filter(ImageFilter.CONTOUR).convert("RGB")

        elif name == "Emboss":
            pil_img = pil_img.filter(ImageFilter.EMBOSS)

        # "Original" -> no change
        return pil_img