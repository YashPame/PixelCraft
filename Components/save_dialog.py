import os
import cv2
import numpy as np
from tkinter import *
from tkinter import ttk, filedialog, messagebox

THEME = "#2f3775"
FORMATS = ["PNG", "JPG", "JPEG"]


class SaveDialog(Toplevel):
    def __init__(self, App):
        super().__init__(App.root)
        self.App = App
        self.Editor = App.editor
        self.doc = self.Editor.active_image

        self.title("Save Image")
        self.resizable(False, False)

        # keep this window on top of the (fullscreen) app and block clicks behind it
        self.transient(App.root)
        self.attributes("-topmost", True)
        self.grab_set()

        # original size of the edited image
        self.orig_h, self.orig_w = self.doc.image.shape[:2]
        self.updating = False   # stops width/height from updating each other forever

        Label(self, text="Save Image", font=("Arial", 16), fg=THEME).pack(pady=10)

        # ----- Format -----
        Label(self, text="Format", font=("Arial", 12), fg=THEME).pack()
        self.format_var = StringVar(value="PNG")
        formatFrame = Frame(self)
        formatFrame.pack(pady=5)
        for fmt in FORMATS:
            Radiobutton(formatFrame, text=fmt, variable=self.format_var, value=fmt,
                        font=("Arial", 11), command=self.FormatChanged).pack(side=LEFT, padx=10)

        # ----- Resolution -----
        Label(self, text="Resolution (pixels)", font=("Arial", 12), fg=THEME).pack(pady=(10, 0))

        sizeFrame = Frame(self)
        sizeFrame.pack(pady=5)

        self.width_var = StringVar(value=str(self.orig_w))
        self.height_var = StringVar(value=str(self.orig_h))

        Label(sizeFrame, text="Width", font=("Arial", 11)).grid(row=0, column=0, padx=5)
        Entry(sizeFrame, textvariable=self.width_var, width=8, font=("Arial", 11)).grid(row=0, column=1, padx=5)
        Label(sizeFrame, text="Height", font=("Arial", 11)).grid(row=0, column=2, padx=5)
        Entry(sizeFrame, textvariable=self.height_var, width=8, font=("Arial", 11)).grid(row=0, column=3, padx=5)

        self.keep_ratio = BooleanVar(value=True)
        Checkbutton(self, text="Keep aspect ratio", variable=self.keep_ratio,
                    font=("Arial", 10)).pack()

        # quick size buttons
        percentFrame = Frame(self)
        percentFrame.pack(pady=5)
        for percent in (100, 75, 50, 25):
            Button(percentFrame, text=f"{percent}%", width=5, font=("Arial", 10),
                   command=lambda p=percent: self.SetPercent(p)).pack(side=LEFT, padx=4)

        # when one size changes, update the other (if keep aspect ratio is on)
        self.width_var.trace_add("write", self.WidthChanged)
        self.height_var.trace_add("write", self.HeightChanged)

        # ----- Quality (JPG only) -----
        Label(self, text="Quality (JPG only)", font=("Arial", 12), fg=THEME).pack(pady=(10, 0))
        self.quality = ttk.Scale(self, from_=10, to=100, orient=HORIZONTAL, length=250)
        self.quality.set(95)
        self.quality.pack(pady=5)

        # ----- Buttons -----
        buttonFrame = Frame(self)
        buttonFrame.pack(pady=15)
        Button(buttonFrame, text="Save", width=10, font=("Arial", 11, "bold"), bg=THEME, fg="white",
               command=self.SaveClicked).pack(side=LEFT, padx=10)
        Button(buttonFrame, text="Cancel", width=10, font=("Arial", 11),
               command=self.destroy).pack(side=LEFT, padx=10)

        self.FormatChanged()
        self.CenterOnApp()

    # ---------------- Helpers ----------------

    def CenterOnApp(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = self.App.root.winfo_x() + (self.App.root.winfo_width() - w) // 2
        y = self.App.root.winfo_y() + (self.App.root.winfo_height() - h) // 2
        self.geometry(f"+{x}+{y}")

    def FormatChanged(self):
        # quality only matters for JPG
        if self.format_var.get() == "PNG":
            self.quality.state(["disabled"])
        else:
            self.quality.state(["!disabled"])

    def SetPercent(self, percent):
        self.updating = True
        self.width_var.set(str(max(1, round(self.orig_w * percent / 100))))
        self.height_var.set(str(max(1, round(self.orig_h * percent / 100))))
        self.updating = False

    def WidthChanged(self, *args):
        if self.updating or not self.keep_ratio.get():
            return
        try:
            w = int(self.width_var.get())
        except ValueError:
            return   # empty or not a number while typing
        self.updating = True
        self.height_var.set(str(max(1, round(w * self.orig_h / self.orig_w))))
        self.updating = False

    def HeightChanged(self, *args):
        if self.updating or not self.keep_ratio.get():
            return
        try:
            h = int(self.height_var.get())
        except ValueError:
            return
        self.updating = True
        self.width_var.set(str(max(1, round(h * self.orig_w / self.orig_h))))
        self.updating = False

    # ---------------- Save ----------------

    def SaveClicked(self):
        # 1. check the size
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
        except ValueError:
            messagebox.showerror("Invalid size", "Width and height must be numbers.", parent=self)
            return

        if width <= 0 or height <= 0 or width > 20000 or height > 20000:
            messagebox.showerror("Invalid size", "Width and height must be between 1 and 20000.", parent=self)
            return

        # 2. ask where to save and the file name (normal Windows "Save As" window)
        ext = self.format_var.get().lower()
        name = os.path.splitext(self.doc.file_name)[0] + "_edited"

        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Image As",
            initialdir=os.path.dirname(self.doc.file_path),
            initialfile=f"{name}.{ext}",
            defaultextension=f".{ext}",
            filetypes=[(f"{ext.upper()} Image", f"*.{ext}")]
        )

        if not path:
            return   # user pressed Cancel in the Save As window

        # make sure the file ends with the chosen format
        path = os.path.splitext(path)[0] + f".{ext}"

        # 3. resize (INTER_AREA looks best when shrinking, INTER_CUBIC when enlarging)
        img = self.doc.image
        if (width, height) != (self.orig_w, self.orig_h):
            if width < self.orig_w:
                method = cv2.INTER_AREA
            else:
                method = cv2.INTER_CUBIC
            img = cv2.resize(img, (width, height), interpolation=method)

        # 4. JPG has no transparency: put transparent parts on a white background
        if ext in ("jpg", "jpeg") and img.ndim == 3 and img.shape[2] == 4:
            alpha = img[:, :, 3:4].astype(np.float32) / 255
            white = np.full_like(img[:, :, :3], 255, dtype=np.float32)
            img = (img[:, :, :3] * alpha + white * (1 - alpha)).astype(np.uint8)

        # 5. save
        if ext == "png":
            params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
        else:
            params = [cv2.IMWRITE_JPEG_QUALITY, int(self.quality.get())]

        # imencode + tofile works with any folder/file name (cv2.imwrite fails on non-English names)
        ok, buffer = cv2.imencode(f".{ext}", img, params)
        if not ok:
            messagebox.showerror("Error", "Could not save the image.", parent=self)
            return

        try:
            buffer.tofile(path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save the image.\n{e}", parent=self)
            return

        self.doc.modified = False   # saved, so Cancel won't ask again
        messagebox.showinfo("Saved", f"Image saved to:\n{path}", parent=self)
        self.destroy()