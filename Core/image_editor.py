import cv2
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk

from Core.image_document import ImageDocument
from tkinter import messagebox

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageTk
import numpy as np

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

    def StartAdjust(self):
        # remember how the image looked before the drag started
        if self.active_image is None:
            return
        self.state_before_adjust = self.GetState()

    def EndAdjust(self):
        # after the drag: add ONE undo entry, but only if something changed
        if self.active_image is None or self.state_before_adjust is None:
            return

        if self.state_before_adjust["adjustments"] != self.active_image.adjustments:
            self.active_image.undo_stack.append(self.state_before_adjust)

            if len(self.active_image.undo_stack) > MAX_HISTORY:
                self.active_image.undo_stack.pop(0)

            self.active_image.redo_stack.clear()

        self.state_before_adjust = None

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

        self.active_image=image
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
            "base_image": self.active_image.base_image.copy(),    # NEW
            "zoom": self.active_image.zoom.get(),
            "adjustments": dict(self.active_image.adjustments)
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
        self.active_image.base_image = state["base_image"]     # NEW
        self.active_image.zoom.set(state["zoom"])
        self.active_image.zoom_percentage.set(f"{round(self.active_image.zoom.get() * 100, 2)}%")
        self.active_image.adjustments = state["adjustments"]   # NEW
        self.SyncSliders()                                     # NEW

        self.ShowImage()

    def Redo(self):
        if self.active_image is None:
            return

        if not self.active_image.redo_stack:
            return

        self.active_image.undo_stack.append(self.GetState())

        state = self.active_image.redo_stack.pop()

        self.active_image.image = state["image"]
        self.active_image.base_image = state["base_image"]
        self.active_image.zoom.set(state["zoom"])
        self.active_image.zoom_percentage.set(f"{round(self.active_image.zoom.get() * 100, 2)}%")

        self.active_image.adjustments = state["adjustments"]
        self.SyncSliders()
        self.ShowImage()

    def Reset(self):
        if self.active_image is None:
            return

        self.SaveState()

        self.active_image.image = self.active_image.orignal_image.copy()
        self.active_image.base_image = self.active_image.orignal_image.copy()
        self.active_image.zoom.set(self.active_image.initial_zoom)
        self.active_image.zoom_percentage.set(f"{round(self.active_image.zoom.get() * 100, 2)}%")

        self.active_image.modified = False

        self.active_image.undo_stack.clear()
        self.active_image.redo_stack.clear()
        
        self.active_image.modified = False
        self.active_image.adjustments = {}   # NEW
        self.SyncSliders()                   # NEW
        self.ShowImage()

    def SyncSliders(self):
        # Move the sliders to match the current image's adjustments
        # The light panel only exists while it is open, so skip if it is closed
        panel = getattr(self.App, "light_panel", None)
        if panel is None or not panel.winfo_exists():
            return
        panel.SetValues(self.active_image.adjustments)

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

        # Always start from the base image (after crop, before adjustments)
        img = self.active_image.base_image

        # Handle grayscale and transparent (PNG) images
        alpha = None
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            alpha = img[:, :, 3]
            img = img[:, :, :3]

        # OpenCV (BGR) -> PIL (RGB)
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        for parameter in ADJUSTMENT_ORDER:
            if parameter in values:
                pil_img = self.LightAdjustment(pil_img, parameter, values[parameter])

        # PIL (RGB) -> OpenCV (BGR)
        result = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        if alpha is not None:
            result = np.dstack([result, alpha])

        self.active_image.image = result
        self.active_image.modified = True
        self.ShowImage()