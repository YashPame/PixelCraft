import cv2
import math
import numpy as np
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageTk

from Core.image_document import ImageDocument

# Order in which adjustments are applied (always the same, whatever the slider order)
ADJUSTMENT_ORDER = ["Auto Enhance", "Exposure", "Brightness", "Contrast", "Highlights", "Shadows",
                    "Saturation", "Warmth", "Tint", "Sharpness", "Vignette"]

# Sliders that are a simple PIL "enhance" (factor 0 = none, 1 = original, 2 = double)
ENHANCERS = {"Brightness": ImageEnhance.Brightness, "Contrast": ImageEnhance.Contrast,
             "Saturation": ImageEnhance.Color, "Sharpness": ImageEnhance.Sharpness}

# Everything saved for Undo / Redo 
STATE_FIELDS = ["base_image", "adjustments", "straighten_source", "straighten_angle",
                "filter_name", "drawing_layer", "drawing_source", "cutout"]

CANVAS_WIDTH = 620
CANVAS_HEIGHT = 620
MAX_HISTORY = 10
MAX_ZOOM = 10.0
MIN_ZOOM = 0.20
ZOOM_STEP = 0.05
FIT_MARGIN = 4      # small gap so a fitted image never shows scrollbars


def Copy(value):
    # copy images and dicts, keep numbers / strings / None as they are
    return value.copy() if hasattr(value, "copy") else value


def ToRGB(img):
    # OpenCV image (gray / BGR / BGRA) -> RGB or RGBA
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    if img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


class Editor:
    def __init__(self, App, canvas):
        self.canvas = canvas
        self.App = App
        self.active_image = None
        self.canvas_image_id = None
        self.state_before_adjust = None

        # where the image is drawn on the canvas (used by crop box and drawing)
        self.image_x = self.image_y = 0
        self.display_width = self.display_height = 0

    # ---------------- Open / Show / Close ----------------

    def OpenImage(self):
        file_path = filedialog.askopenfilename(title="Open Image", filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if not file_path:
            return None

        try:
            image = ImageDocument(file_path)
        except:
            messagebox.showerror("Error", "Something Went Wrong, Unable to open File...")
            return None

        image.cutout = None            # subject with transparent background (set by RemoveBackground)
        self.active_image = image
        self.App.hasImage.set(True)    # show the canvas first, so its real size can be measured
        self.SetInitialZoom()
        self.SyncSliders()
        self.ShowImage()
        return image

    def ShowImage(self, original=False):
        # original=True shows the untouched photo (Before/After button)
        doc = self.active_image
        if doc is None:
            return

        image = doc.orignal_image if original else doc.image
        pil_image = Image.fromarray(ToRGB(image))

        zoom = doc.zoom.get()
        if original and image.shape[:2] != doc.image.shape[:2]:
            zoom = self.FitZoom(image)        # cropped / rotated since: fit the original on its own
        if zoom != 1.0:
            pil_image = pil_image.resize((int(pil_image.width * zoom), int(pil_image.height * zoom)))

        photo = ImageTk.PhotoImage(pil_image)

        # measure the canvas while the OLD picture is still showing (no empty frame on screen)
        self.canvas.update_idletasks()
        canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        w, h = pil_image.width, pil_image.height

        # center the image, remember where it is
        self.image_x = max((canvas_w - w) // 2, 0)
        self.image_y = max((canvas_h - h) // 2, 0)
        self.display_width, self.display_height = w, h

        # swap the picture inside the SAME canvas item instead of deleting and re-creating it
        # (deleting first showed an empty canvas for a moment = flicker while sliding)
        if self.canvas_image_id is not None and self.canvas.type(self.canvas_image_id) == "image":
            self.canvas.itemconfig(self.canvas_image_id, image=photo)
            self.canvas.coords(self.canvas_image_id, self.image_x, self.image_y)
        else:
            self.canvas_image_id = self.canvas.create_image(self.image_x, self.image_y, anchor="nw", image=photo)
            self.canvas.tag_lower(self.canvas_image_id)          # crop box / masks stay on top
        doc.photo_image = photo      # keep it alive (only now, so the old one is never missing)

        self.canvas.configure(scrollregion=(0, 0, max(canvas_w, self.image_x + w), max(canvas_h, self.image_y + h)))

        if original:
            # no crop box / masks on top of the "before" photo (they come back on release)
            for item in self.canvas.find_all():
                if item != self.canvas_image_id:
                    self.canvas.delete(item)
            return

        # open panels draw their marks again on top of the image (crop box, eraser mask, ...)
        if self.GetPanel("crop_panel"):
            self.App.crop_panel.DrawCropBox()
        if self.GetPanel("eraser_panel"):
            self.App.eraser_panel.DrawMask()
        if self.GetPanel("bg_panel"):
            self.App.bg_panel.DrawBox()

    def CloseImage(self):
        # Discard the image and go back to the "Open Image" screen
        self.active_image = None
        self.canvas.delete("all")
        self.canvas_image_id = None
        self.App.hasImage.set(False)   # ActionBar and App update themselves from this

    # ---------------- Zoom / Reset ----------------

    def SetZoom(self, zoom):
        self.active_image.zoom.set(zoom)
        self.active_image.zoom_percentage.set(f"{round(zoom * 100, 2)}%")

    def FitZoom(self, image):
        # zoom that fits the whole image inside the canvas (big images shrink, small ones grow)
        self.canvas.update_idletasks()
        canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if canvas_w < 50 or canvas_h < 50:                 # canvas not on screen yet
            canvas_w, canvas_h = CANVAS_WIDTH, CANVAS_HEIGHT

        h, w = image.shape[:2]
        return min((canvas_w - FIT_MARGIN) / w, (canvas_h - FIT_MARGIN) / h, MAX_ZOOM)

    def SetInitialZoom(self):
        zoom = self.FitZoom(self.active_image.image)
        self.active_image.initial_zoom = zoom
        self.SetZoom(zoom)

    def FitToScreen(self):
        # "Fit" button / Ctrl+0
        if self.active_image is None:
            return
        self.SetInitialZoom()
        self.ShowImage()

    def ShowOriginal(self, show):
        # Before/After button: show=True while the button is held down
        if self.active_image is not None:
            self.ShowImage(original=show)

    def ChangeZoom(self, step):
        if self.active_image is None:
            return
        zoom = self.active_image.zoom.get()
        if (step > 0 and zoom >= MAX_ZOOM) or (step < 0 and zoom <= MIN_ZOOM):
            return
        new_zoom = min(zoom + step, MAX_ZOOM) if step > 0 else max(zoom + step, MIN_ZOOM)
        self.SetZoom(new_zoom)
        self.ShowImage()

    def ZoomIn(self):
        self.ChangeZoom(ZOOM_STEP)

    def ZoomOut(self):
        self.ChangeZoom(-ZOOM_STEP)

    def Reset(self):
        if self.active_image is None:
            return
        doc = self.active_image
        doc.ResetEdits()
        doc.cutout = None
        doc.undo_stack.clear()
        doc.redo_stack.clear()
        self.SetInitialZoom()
        self.SyncSliders()
        self.ShowImage()

    # ---------------- Undo / Redo ----------------

    def GetState(self):
        doc = self.active_image
        return {name: Copy(getattr(doc, name)) for name in STATE_FIELDS}

    def RestoreState(self, state):
        doc = self.active_image
        old_size = doc.base_image.shape[:2]
        for name in STATE_FIELDS:
            setattr(doc, name, state[name])
        self.RenderImage()
        if doc.base_image.shape[:2] != old_size:
            self.SetInitialZoom()   # undo / redo of a crop or rotate: fit the new size
        self.SyncSliders()
        self.ShowImage()

    def PushUndo(self, state):
        stack = self.active_image.undo_stack
        stack.append(state)
        if len(stack) > MAX_HISTORY:
            stack.pop(0)
        self.active_image.redo_stack.clear()

    def SaveState(self):
        self.PushUndo(self.GetState())

    def UndoRedo(self, from_stack, to_stack):
        # take the last state from one stack, save the current one on the other
        if self.active_image is None or not from_stack:
            return
        to_stack.append(self.GetState())
        self.RestoreState(from_stack.pop())

    def Undo(self):
        if self.active_image is not None:
            self.UndoRedo(self.active_image.undo_stack, self.active_image.redo_stack)

    def Redo(self):
        if self.active_image is not None:
            self.UndoRedo(self.active_image.redo_stack, self.active_image.undo_stack)

    def StartAdjust(self):
        # remember how the image looked before a slider drag started
        if self.active_image is not None:
            self.state_before_adjust = self.GetState()

    def EndAdjust(self):
        # after the drag: add ONE undo entry, but only if something changed
        before = self.state_before_adjust
        if self.active_image is None or before is None:
            return
        doc = self.active_image
        if before["adjustments"] != doc.adjustments or before["straighten_angle"] != doc.straighten_angle:
            self.PushUndo(before)
        self.state_before_adjust = None

    # ---------------- Panels ----------------

    def GetPanel(self, name):
        # the panel if it is open, else None
        panel = getattr(self.App, name, None)
        return panel if panel is not None and panel.winfo_exists() else None

    def SyncSliders(self):
        # Move the sliders in the open panel to match the current image
        doc = self.active_image
        if doc is None:
            return
        if self.GetPanel("light_panel"):
            self.App.light_panel.SetValues(doc.adjustments)
        if self.GetPanel("crop_panel"):
            self.App.crop_panel.SetAngle(doc.straighten_angle)
        if self.GetPanel("filters_panel"):
            self.App.filters_panel.Refresh()

    # ---------------- Rotate / Flip / Crop / Straighten ----------------

    def Transform(self, func, refit=False, layer_func=None, cutout_func=None):
        # apply a change to the photo, and the same change (or layer_func / cutout_func)
        # to the drawing layer and to the cut-out subject, so they always line up
        doc = self.active_image
        self.SaveState()
        doc.base_image = func(doc.base_image)
        if doc.drawing_layer is not None:
            doc.drawing_layer = (layer_func or func)(doc.drawing_layer)
        if doc.cutout is not None:
            doc.cutout = (cutout_func or func)(doc.cutout)
        self.ClearStraighten()
        self.RenderImage()
        if refit:
            self.SetInitialZoom()   # fit the new size in the canvas
        self.ShowImage()

    def Rotate90(self, clockwise=True):
        if self.active_image is None:
            return
        code = cv2.ROTATE_90_CLOCKWISE if clockwise else cv2.ROTATE_90_COUNTERCLOCKWISE
        self.Transform(lambda img: cv2.rotate(img, code))

    def Flip(self, horizontal=True):
        if self.active_image is None:
            return
        # 1 = flip left/right, 0 = flip up/down
        self.Transform(lambda img: cv2.flip(img, 1 if horizontal else 0))

    def Crop(self, left, top, right, bottom):
        # left/top/right/bottom are fractions of the image (0 to 1)
        if self.active_image is None:
            return
        h, w = self.active_image.base_image.shape[:2]
        x1, y1, x2, y2 = int(left * w), int(top * h), int(right * w), int(bottom * h)
        if x2 - x1 < 2 or y2 - y1 < 2:
            return
        self.Transform(lambda img: img[y1:y2, x1:x2].copy(), refit=True)

    def Straighten(self, angle):
        # Always rotates from the image before straightening, so 10° then 5° gives 5°, not 15°
        doc = self.active_image
        if doc is None or angle == doc.straighten_angle:
            return

        if doc.straighten_source is None:
            doc.straighten_source = doc.base_image.copy()
            doc.drawing_source = Copy(doc.drawing_layer)
            doc.cutout = None      # straightened photo no longer matches the cut-out subject

        doc.straighten_angle = angle
        doc.base_image = self.RotateAndFill(doc.straighten_source, angle)
        if doc.drawing_source is not None:
            doc.drawing_layer = self.RotateAndFill(doc.drawing_source, angle, fill_edges=False)

        self.RenderImage()
        self.ShowImage()

    def RotateAndFill(self, img, angle, fill_edges=True):
        # Rotate by any angle and zoom in just enough so no empty corners show
        if angle == 0:
            return img.copy()

        h, w = img.shape[:2]
        a = math.radians(abs(angle))
        scale = max(math.cos(a) + (h / w) * math.sin(a), math.cos(a) + (w / h) * math.sin(a))

        # the drawing layer uses transparent edges instead of repeated pixels
        border = cv2.BORDER_REPLICATE if fill_edges else cv2.BORDER_CONSTANT

        # OpenCV uses positive = anticlockwise, so -angle makes positive = clockwise
        matrix = cv2.getRotationMatrix2D((w / 2, h / 2), -angle, scale)
        return cv2.warpAffine(img, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=border, borderValue=0)

    def ClearStraighten(self):
        # After rotate/flip/crop/draw the straighten angle becomes part of the image
        doc = self.active_image
        doc.straighten_source = doc.drawing_source = None
        doc.straighten_angle = 0
        self.SyncSliders()

    # ---------------- Magic Eraser / Background Remover (OpenCV) ----------------

    def MagicErase(self, mask, radius=5):
        # mask: white where the user painted (same size as the image). Fills it from the surroundings.
        doc = self.active_image
        if doc is None or mask is None or not mask.any():
            return

        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=2)   # cover the object edges too

        def inpaint(img):
            if img.ndim == 2 or img.shape[2] == 3:
                return cv2.inpaint(img, mask, radius, cv2.INPAINT_TELEA)
            # transparent PNG: fill the color and the transparency separately
            color = cv2.inpaint(np.ascontiguousarray(img[:, :, :3]), mask, radius, cv2.INPAINT_TELEA)
            alpha = cv2.inpaint(np.ascontiguousarray(img[:, :, 3]), mask, radius, cv2.INPAINT_TELEA)
            return np.dstack([color, alpha])

        def clear_drawing(layer):
            # pen strokes under the mask are removed too
            layer = layer.copy()
            layer[mask > 0, 3] = 0
            return layer

        self.Transform(inpaint, layer_func=clear_drawing)

    def RemoveBackground(self, left, top, right, bottom, iterations=5):
        # box (fractions 0-1) around the subject -> everything outside the subject becomes transparent
        doc = self.active_image
        if doc is None:
            return False

        img = doc.base_image
        h, w = img.shape[:2]
        x1, y1, x2, y2 = int(left * w), int(top * h), int(right * w), int(bottom * h)
        if x2 - x1 < 10 or y2 - y1 < 10:
            return False

        # GrabCut needs a BGR image
        if img.ndim == 2:
            bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            bgr = np.ascontiguousarray(img[:, :, :3])

        # work on a smaller copy (GrabCut is slow on big photos), max 600 px
        scale = min(1.0, 600 / max(h, w))
        small = cv2.resize(bgr, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
        rect = (int(x1 * scale), int(y1 * scale), max(1, int((x2 - x1) * scale)), max(1, int((y2 - y1) * scale)))

        gc_mask = np.zeros(small.shape[:2], np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        try:
            cv2.grabCut(small, gc_mask, rect, bgd_model, fgd_model, iterations, cv2.GC_INIT_WITH_RECT)
        except cv2.error:
            return False

        # subject = "sure" + "probably" foreground
        subject = np.where((gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
        if not subject.any():
            return False

        # back to full size, with slightly soft edges
        alpha = cv2.resize(subject, (w, h), interpolation=cv2.INTER_LINEAR)
        alpha = cv2.GaussianBlur(alpha, (5, 5), 0)

        def cut_out(image):
            color = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if image.ndim == 2 else image[:, :, :3]
            new_alpha = alpha if image.ndim == 2 or image.shape[2] == 3 else np.minimum(alpha, image[:, :, 3])
            return np.dstack([color, new_alpha])

        self.Transform(cut_out, layer_func=lambda layer: layer, cutout_func=lambda c: c)   # drawing stays as it is
        self.active_image.cutout = self.active_image.base_image.copy()    # keep the subject for "new background"
        return True

    def SetBackground(self, mode, color_bgr=None, image_path=None):
        # Put something behind the cut-out subject:
        #   "none"  -> transparent again       "color" -> one solid color
        #   "blur"  -> the original photo, blurred (portrait look)
        #   "image" -> another photo, filling the whole frame
        # Always starts from the cut-out, so you can switch backgrounds as often as you like.
        doc = self.active_image
        if doc is None or doc.cutout is None or doc.cutout.shape[:2] != doc.base_image.shape[:2]:
            return False

        cutout = doc.cutout
        h, w = cutout.shape[:2]

        if mode == "none":
            result = cutout.copy()
        else:
            if mode == "color":
                background = np.full((h, w, 3), color_bgr, np.uint8)
            elif mode == "blur":
                # cut-out keeps the original colors everywhere, only the transparency changed
                strength = max(15, (max(h, w) // 40) | 1)            # odd size, bigger photo = more blur
                background = cv2.GaussianBlur(np.ascontiguousarray(cutout[:, :, :3]), (strength, strength), 0)
            elif mode == "image":
                # np.fromfile + imdecode also works with Hindi / non-English folder names on Windows
                background = cv2.imdecode(np.fromfile(image_path, np.uint8), cv2.IMREAD_COLOR)
                if background is None:
                    return False
                # "cover": scale so it fills the frame, then cut off what sticks out (centered)
                bh, bw = background.shape[:2]
                scale = max(w / bw, h / bh)
                background = cv2.resize(background, (max(w, round(bw * scale)), max(h, round(bh * scale))),
                                        interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
                top, left = (background.shape[0] - h) // 2, (background.shape[1] - w) // 2
                background = background[top:top + h, left:left + w]
            else:
                return False

            alpha = cutout[:, :, 3:4].astype(np.float32) / 255     # 1 = subject, 0 = background
            result = (cutout[:, :, :3] * alpha + background * (1 - alpha)).astype(np.uint8)

        self.Transform(lambda img: result, layer_func=lambda layer: layer, cutout_func=lambda c: c)
        return True

    # ---------------- Light / Color adjustments ----------------

    def ApplyCurve(self, pil_img, func):
        # lookup table (old value 0-255 -> new value) applied to every channel
        table = [int(min(255, max(0, func(x)))) for x in range(256)]
        return pil_img.point(table * len(pil_img.getbands()))

    def ShiftChannels(self, pil_img, r=0, g=0, b=0):
        # add / remove some red, green or blue
        channels = list(pil_img.split())
        for i, amount in enumerate((r, g, b)):
            if amount:
                channels[i] = self.ApplyCurve(channels[i], lambda x, a=amount: x + a)
        return Image.merge("RGB", channels)

    def LightAdjustment(self, pil_img, parameter, value):
        # pil_img is an RGB PIL image, value is between -100 and 100
        if parameter in ENHANCERS:
            # -100 -> 0.0, 0 -> 1.0 (no change), +100 -> 2.0
            return ENHANCERS[parameter](pil_img).enhance(1 + value / 100)

        if parameter == "Exposure":
            # gamma curve: brightens/darkens mid-tones without blowing out whites
            gamma = 2 ** (-value / 100)
            return self.ApplyCurve(pil_img, lambda x: 255 * (x / 255) ** gamma)

        if parameter == "Highlights":   # only bright values (above 128)
            return self.ApplyCurve(pil_img, lambda x: x + value * max(0, (x - 128) / 127))

        if parameter == "Shadows":      # only dark values (below 128)
            return self.ApplyCurve(pil_img, lambda x: x + value * max(0, (128 - x) / 128))

        if parameter == "Warmth":       # more red + less blue = warmer
            return self.ShiftChannels(pil_img, r=value / 2, b=-value / 2)

        if parameter == "Tint":         # less green = magenta, more green = green
            return self.ShiftChannels(pil_img, g=-value / 2)

        if parameter == "Vignette":
            strength = abs(value) / 100
            # radial_gradient: black in the center, white at the edges
            mask = Image.radial_gradient("L").filter(ImageFilter.GaussianBlur(4)).resize(pil_img.size)
            # keep the center clean, apply the effect mostly at the edges
            mask = mask.point(lambda x: int((x / 255) ** 2 * 255 * strength))
            # negative = dark edges, positive = white edges
            edge = Image.new("RGB", pil_img.size, (0, 0, 0) if value < 0 else (255, 255, 255))
            return Image.composite(edge, pil_img, mask)

        if parameter == "Auto Enhance":
            enhanced = ImageOps.autocontrast(pil_img, cutoff=1)
            enhanced = ImageEnhance.Color(enhanced).enhance(1.2)
            return Image.blend(pil_img, enhanced, value / 100)

        return pil_img

    def ApplyAdjustments(self, values, save_state=True):
        if self.active_image is None:
            return

        values = {k: v for k, v in values.items() if v != 0}   # keep only sliders that are not 0
        if values == self.active_image.adjustments:
            return                                              # nothing changed

        if save_state:
            self.SaveState()
        self.active_image.adjustments = values
        self.RenderImage()
        self.ShowImage()

    def RenderImage(self):
        # image = (base_image + adjustments + filter) + drawing on top
        doc = self.active_image
        doc.processed_image = self.ProcessImage(doc.base_image, doc.adjustments, doc.filter_name)
        doc.image = self.CompositeDrawing(doc.processed_image, doc.drawing_layer)
        doc.modified = True

    def ProcessImage(self, img, adjustments, filter_name):
        # Works on any size image: used for the real image AND the filter previews
        if not adjustments and filter_name == "Original":
            return img.copy()

        # grayscale and transparent (PNG) images
        alpha = None
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            alpha, img = img[:, :, 3], img[:, :, :3]

        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        for parameter in ADJUSTMENT_ORDER:                       # 1. sliders
            if parameter in adjustments:
                pil_img = self.LightAdjustment(pil_img, parameter, adjustments[parameter])
        pil_img = self.ApplyFilter(pil_img, filter_name)         # 2. filter

        result = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return result if alpha is None else np.dstack([result, alpha])

    # ---------------- Filters ----------------

    def SetFilter(self, filter_name):
        # Called when a filter preview is clicked
        if self.active_image is None or filter_name == self.active_image.filter_name:
            return
        self.SaveState()
        self.active_image.filter_name = filter_name
        self.RenderImage()
        self.ShowImage()

    def ApplyFilter(self, pil_img, name):
        # pil_img is an RGB PIL image, "Original" -> no change
        if name in ("Grayscale", "Sepia", "Vintage", "Noir", "Sketch"):
            gray = ImageOps.grayscale(pil_img)

        if name == "Grayscale":
            return gray.convert("RGB")
        if name == "Sepia":       # dark brown shadows, cream highlights
            return ImageOps.colorize(gray, black="#2e1f0f", white="#f5e6c8")
        if name == "Vintage":     # half sepia mixed with the original, slightly faded
            sepia = ImageOps.colorize(gray, black="#3b2a1a", white="#fff2d5")
            return ImageEnhance.Contrast(Image.blend(pil_img, sepia, 0.5)).enhance(0.85)
        if name == "Noir":        # strong black & white
            return ImageEnhance.Contrast(ImageOps.autocontrast(gray, cutoff=2)).enhance(1.5).convert("RGB")
        if name == "Vivid":
            return ImageEnhance.Contrast(ImageEnhance.Color(pil_img).enhance(1.6)).enhance(1.15)
        if name == "Warm":
            return self.ShiftChannels(pil_img, r=25, b=-25)
        if name == "Cool":
            return self.ShiftChannels(pil_img, r=-20, b=25)
        if name == "Fade":
            pil_img = ImageEnhance.Contrast(pil_img).enhance(0.75)
            pil_img = ImageEnhance.Brightness(pil_img).enhance(1.08)
            return ImageEnhance.Color(pil_img).enhance(0.8)
        if name == "Invert":
            return ImageOps.invert(pil_img)
        if name == "Sketch":      # pencil-like outlines on white
            return gray.filter(ImageFilter.CONTOUR).convert("RGB")
        if name == "Emboss":
            return pil_img.filter(ImageFilter.EMBOSS)
        return pil_img

    # ---------------- Drawing ----------------

    def CompositeDrawing(self, img, layer):
        # Put the transparent drawing layer on top of the image
        if layer is None or not layer[:, :, 3].any():
            return img

        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        alpha = layer[:, :, 3:4].astype(np.float32) / 255      # 0 = no drawing, 1 = solid drawing
        result = img.copy()
        result[:, :, :3] = (layer[:, :, :3] * alpha + img[:, :, :3] * (1 - alpha)).astype(np.uint8)

        if img.shape[2] == 4:   # transparent PNG: drawing makes those pixels visible
            result[:, :, 3] = np.maximum(img[:, :, 3], layer[:, :, 3])
        return result

    def AddStroke(self, points, color_bgr, size, opacity, erase=False):
        # points: list of (x, y) in IMAGE pixels, size: brush size in IMAGE pixels
        doc = self.active_image
        if doc is None or not points or (erase and doc.drawing_layer is None):
            return   # no image / no stroke / nothing to erase

        # only work on the small area around the stroke (much faster on big photos)
        h, w = doc.base_image.shape[:2]
        pad = size // 2 + 2
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        x0, y0 = max(0, min(xs) - pad), max(0, min(ys) - pad)
        x1, y1 = min(w, max(xs) + pad + 1), min(h, max(ys) + pad + 1)
        if x0 >= x1 or y0 >= y1:
            return   # stroke was completely outside the image

        self.SaveState()
        self.ClearStraighten()   # the current angle becomes part of the image

        if doc.drawing_layer is None:
            doc.drawing_layer = np.zeros((h, w, 4), dtype=np.uint8)

        # 1. draw the stroke shape as white on black (the "mask")
        mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
        local = np.array([(x - x0, y - y0) for x, y in points], dtype=np.int32)
        if len(local) == 1:
            cv2.circle(mask, (int(local[0][0]), int(local[0][1])), max(1, size // 2), 255, -1, cv2.LINE_AA)
        else:
            cv2.polylines(mask, [local.reshape(-1, 1, 2)], False, 255, thickness=max(1, size), lineType=cv2.LINE_AA)

        # how strong the stroke is at each pixel (0 to 1)
        strength = (mask.astype(np.float32) / 255 * opacity)[:, :, None]
        region = doc.drawing_layer[y0:y1, x0:x1].astype(np.float32)
        old_alpha = region[:, :, 3:4] / 255

        if erase:
            # 2a. eraser: make the drawing transparent where the stroke is
            region[:, :, 3:4] = old_alpha * (1 - strength) * 255
        else:
            # 2b. pen: put the new color "over" the old drawing
            new_alpha = strength + old_alpha * (1 - strength)
            color = np.array(color_bgr, dtype=np.float32)
            region[:, :, :3] = (color * strength + region[:, :, :3] * old_alpha * (1 - strength)) / np.maximum(new_alpha, 1e-6)
            region[:, :, 3:4] = new_alpha * 255

        doc.drawing_layer[y0:y1, x0:x1] = np.clip(region, 0, 255).astype(np.uint8)

        # only the drawing changed: update just the stroke area of the shown image (fast)
        if doc.image is doc.processed_image or doc.image.ndim == 2:
            doc.image = self.CompositeDrawing(doc.processed_image, doc.drawing_layer)
        else:
            doc.image[y0:y1, x0:x1] = self.CompositeDrawing(doc.processed_image[y0:y1, x0:x1],
                                                            doc.drawing_layer[y0:y1, x0:x1])
        doc.modified = True
        self.ShowImage()

    def ClearDrawing(self):
        doc = self.active_image
        if doc is None or doc.drawing_layer is None or not doc.drawing_layer[:, :, 3].any():
            return
        self.SaveState()
        doc.drawing_layer = doc.drawing_source = None
        doc.image = doc.processed_image.copy()
        self.ShowImage()