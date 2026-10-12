import os
import cv2
import numpy as np
from tkinter import *
from tkinter import ttk, filedialog, messagebox

FORMATS = ["PNG", "JPG", "JPEG", "BMP"]


class SaveDialog(Toplevel):
    def __init__(self, App):
        super().__init__(App.root)
        self.App = App
        self.Editor = App.editor
        self.doc = self.Editor.active_image

        self.title("Save Image")
        self.resizable(False, False)

        t = self.t = App.theme                     
        self.config(bg=t["sidebar"])

        self.transient(App.root)
        self.attributes("-topmost", True)
        self.grab_set()

        self.orig_h, self.orig_w = self.doc.image.shape[:2]
        self.updating = False   

        Label(self, text="Save Image", font=self.App.adjust_font(16, bold=True),
              bg=t["sidebar"], fg=t["accent"]).pack(anchor="w", padx=24, pady=(18, 0))
        Label(self, text=f"{self.doc.file_name}  ·  {self.orig_w} × {self.orig_h} px", font=self.App.adjust_font(10),
              bg=t["sidebar"], fg=t["muted"]).pack(anchor="w", padx=24, pady=(0, 4))

        self.SectionLabel("Format")
        self.format_var = StringVar(value="PNG")
        formatFrame = Frame(self, bg=t["sidebar"])
        formatFrame.pack(anchor="w", padx=24, pady=(8, 0))
        for fmt in FORMATS:
            Radiobutton(formatFrame, text=fmt, variable=self.format_var, value=fmt, command=self.FormatChanged,
                        indicatoron=0, width=8, pady=5, font=self.App.adjust_font(10, bold=True),
                        bg=t["surface"], fg=t["text"], selectcolor=t["accent_light"],
                        activebackground=t["accent_light"], activeforeground=t["accent"],
                        relief=FLAT, offrelief=FLAT, bd=0, cursor="hand2",
                        highlightthickness=1, highlightbackground=t["border"]).pack(side=LEFT, padx=(0, 8))

        self.SectionLabel("Resolution (pixels)")

        sizeFrame = Frame(self, bg=t["sidebar"])
        sizeFrame.pack(anchor="w", padx=24, pady=(8, 0))

        self.width_var = StringVar(value=str(self.orig_w))
        self.height_var = StringVar(value=str(self.orig_h))

        entry_style = dict(width=8, font=self.App.adjust_font(11), bg=t["surface"], fg=t["text"], relief=FLAT,
                           highlightthickness=1, highlightbackground=t["border"], highlightcolor=t["accent"],
                           insertbackground=t["accent"], justify=CENTER)
        Label(sizeFrame, text="Width", font=self.App.adjust_font(10), bg=t["sidebar"], fg=t["text"]).grid(row=0, column=0, padx=(0, 6))
        Entry(sizeFrame, textvariable=self.width_var, **entry_style).grid(row=0, column=1, ipady=4)
        Label(sizeFrame, text="×", font=self.App.adjust_font(11, bold=True), bg=t["sidebar"], fg=t["muted"]).grid(row=0, column=2, padx=8)
        Label(sizeFrame, text="Height", font=self.App.adjust_font(10), bg=t["sidebar"], fg=t["text"]).grid(row=0, column=3, padx=(0, 6))
        Entry(sizeFrame, textvariable=self.height_var, **entry_style).grid(row=0, column=4, ipady=4)

        self.keep_ratio = BooleanVar(value=True)
        Checkbutton(self, text="Keep aspect ratio", variable=self.keep_ratio, font=self.App.adjust_font(10),
                    bg=t["sidebar"], fg=t["text"], activebackground=t["sidebar"], activeforeground=t["accent"],
                    selectcolor=t["surface"], bd=0, highlightthickness=0, cursor="hand2").pack(anchor="w", padx=20, pady=(8, 0))

        percentFrame = Frame(self, bg=t["sidebar"])
        percentFrame.pack(anchor="w", padx=24, pady=(8, 0))
        for percent in (100, 75, 50, 25):
            Button(percentFrame, text=f"{percent}%", width=5, font=self.App.adjust_font(10, bold=True),
                   bg=t["accent_light"], fg=t["accent"], activebackground=t["trough"], activeforeground=t["accent"],
                   relief=FLAT, bd=0, pady=3, cursor="hand2",
                   command=lambda p=percent: self.SetPercent(p)).pack(side=LEFT, padx=(0, 8))

        self.width_var.trace_add("write", self.WidthChanged)
        self.height_var.trace_add("write", self.HeightChanged)

        qualityTitle = self.SectionLabel("Quality (JPG only)")
        self.QualityLabel = Label(qualityTitle, text="95", font=self.App.adjust_font(9, bold=True),
                                  bg=t["accent_light"], fg=t["accent"], width=4)
        self.QualityLabel.pack(side=RIGHT)

        self.quality = self.App.CreateSlider(self, from_=10, to=100, length=300,
                                             command=lambda v: self.QualityLabel.config(text=str(int(float(v)))))
        self.quality.set(95)
        self.quality.pack(anchor="w", padx=24, pady=(10, 0))

        Frame(self, bg=t["border"], height=1).pack(fill=X, padx=24, pady=(18, 0))
        buttonFrame = Frame(self, bg=t["sidebar"])
        buttonFrame.pack(fill=X, padx=24, pady=(14, 20))
        Button(buttonFrame, text="Cancel", width=10, font=self.App.adjust_font(11, bold=True),
               bg=t["surface"], fg=t["danger"], activebackground="#fbeaea", activeforeground=t["danger"],
               relief=FLAT, bd=0, pady=6, cursor="hand2", highlightthickness=1, highlightbackground=t["border"],
               command=self.destroy).pack(side=RIGHT)
        Button(buttonFrame, text="Save", width=10, font=self.App.adjust_font(11, bold=True),
               bg=t["accent"], fg="white", activebackground=t["accent_hover"], activeforeground="white",
               relief=FLAT, bd=0, pady=6, cursor="hand2",
               command=self.SaveClicked).pack(side=RIGHT, padx=(0, 10))

        self.FormatChanged()
        self.CenterOnApp()


    def SectionLabel(self, text):
        t = self.t
        Frame(self, bg=t["border"], height=1).pack(fill=X, padx=24, pady=(14, 0))
        row = Frame(self, bg=t["sidebar"])
        row.pack(fill=X, padx=24, pady=(10, 0))
        Label(row, text=text, font=self.App.adjust_font(11, bold=True), bg=t["sidebar"], fg=t["text"]).pack(side=LEFT)
        return row

    def CenterOnApp(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = self.App.root.winfo_x() + (self.App.root.winfo_width() - w) // 2
        y = self.App.root.winfo_y() + (self.App.root.winfo_height() - h) // 2
        self.geometry(f"+{x}+{y}")

    def FormatChanged(self):
        t = self.t
        if self.format_var.get() not in ("JPG", "JPEG"):
            self.quality.config(state=DISABLED, bg=t["muted"])       
            self.QualityLabel.config(bg=t["trough"], fg=t["muted"])
        else:
            self.quality.config(state=NORMAL, bg=t["accent"])
            self.QualityLabel.config(bg=t["accent_light"], fg=t["accent"])

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
            return  
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

    def SaveClicked(self):
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
        except ValueError:
            messagebox.showerror("Invalid size", "Width and height must be numbers.", parent=self)
            return

        if width <= 0 or height <= 0 or width > 20000 or height > 20000:
            messagebox.showerror("Invalid size", "Width and height must be between 1 and 20000.", parent=self)
            return

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
            return   

        path = os.path.splitext(path)[0] + f".{ext}"

        img = self.doc.image
        if (width, height) != (self.orig_w, self.orig_h):
            if width < self.orig_w:
                method = cv2.INTER_AREA
            else:
                method = cv2.INTER_CUBIC
            img = cv2.resize(img, (width, height), interpolation=method)

        if ext in ("jpg", "jpeg", "bmp") and img.ndim == 3 and img.shape[2] == 4:
            alpha = img[:, :, 3:4].astype(np.float32) / 255
            white = np.full_like(img[:, :, :3], 255, dtype=np.float32)
            img = (img[:, :, :3] * alpha + white * (1 - alpha)).astype(np.uint8)

        if ext == "png":
            params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
        elif ext == "bmp":
            params = []                     
        else:
            params = [cv2.IMWRITE_JPEG_QUALITY, int(self.quality.get())]

        ok, buffer = cv2.imencode(f".{ext}", img, params)
        if not ok:
            messagebox.showerror("Error", "Could not save the image.", parent=self)
            return

        try:
            buffer.tofile(path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save the image.\n{e}", parent=self)
            return

        self.doc.modified = False   
        messagebox.showinfo("Saved", f"Image saved to:\n{path}", parent=self)
        self.destroy()