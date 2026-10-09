from tkinter import *
from tkinter import filedialog, colorchooser

# quick background colors (hex)
BG_COLORS = ["#ffffff", "#000000", "#e9ecf3", "#2f3775", "#5aa9e6", "#7fc8a9", "#f6d365", "#f4a6b7"]


class BackgroundRemover(Frame):
    # Background Remover: draw a box around the subject, everything else becomes transparent,
    # then pick a new background (none, color, blur or an image)
    def __init__(self, App, PanelFrame):
        self.t = App.theme                          # colors from main.py
        t = self.t
        super().__init__(PanelFrame, bg=t["sidebar"])
        self.App = App
        self.Editor = App.editor
        self.canvas = self.Editor.canvas

        self.box = None            # [left, top, right, bottom] as fractions of the image, None = no box
        self.start_x = 0
        self.start_y = 0

        # ----- title -----
        Label(self, text="Remove Background", font=self.App.adjust_font(16, bold=True),
              bg=t["sidebar"], fg=t["accent"]).pack(anchor="w", padx=20, pady=(18, 0))
        Label(self, text="Keep the subject, replace or remove the rest", font=self.App.adjust_font(10),
              bg=t["sidebar"], fg=t["muted"]).pack(anchor="w", padx=20, pady=(0, 6))

        # ----- Select subject -----
        section = self.Section("Select Subject")
        Label(section, text="Click and drag a box around the person or object you want to keep. "
                            "A tight box gives a cleaner result.",
              font=self.App.adjust_font(10), bg=t["sidebar"], fg=t["muted"],
              wraplength=self.App.scale_x(320), justify=LEFT).pack(anchor="w", pady=(4, 10))

        buttons = Frame(section, bg=t["sidebar"])
        buttons.pack(fill=X)
        Button(buttons, text="Clear Box", font=self.App.adjust_font(10, bold=True),
               bg=t["accent_light"], fg=t["accent"], activebackground=t["trough"], activeforeground=t["accent"],
               relief=FLAT, bd=0, pady=6, cursor="hand2", command=self.ClearBox).pack(side=LEFT, expand=True, fill=X, padx=(0, 6))
        Button(buttons, text="Remove Background", font=self.App.adjust_font(11, bold=True),
               bg=t["accent"], fg="#ffffff", activebackground=t["accent_hover"], activeforeground="#ffffff",
               relief=FLAT, bd=0, pady=6, cursor="hand2", command=self.Remove).pack(side=LEFT, expand=True, fill=X, padx=(6, 0))

        # status line ("Removing background..." / errors)
        self.Status = Label(section, text="", font=self.App.adjust_font(10, bold=True),
                            bg=t["sidebar"], fg=t["accent"])
        self.Status.pack(anchor="w", pady=(10, 0))

        # ----- New background -----
        section = self.Section("New Background")
        Label(section, text="After removing, pick what goes behind the subject. You can switch any time.",
              font=self.App.adjust_font(9), bg=t["sidebar"], fg=t["muted"],
              wraplength=self.App.scale_x(320), justify=LEFT).pack(anchor="w", pady=(2, 8))

        options = Frame(section, bg=t["sidebar"])
        options.pack(fill=X)
        for col, (text, command) in enumerate([("Transparent", lambda: self.ApplyBackground("none")),
                                               ("Blur", lambda: self.ApplyBackground("blur")),
                                               ("Image...", self.PickImage)]):
            Button(options, text=text, font=self.App.adjust_font(10, bold=True),
                   bg=t["surface"], fg=t["text"], activebackground=t["accent_light"], activeforeground=t["accent"],
                   relief=FLAT, bd=0, pady=5, cursor="hand2", highlightthickness=1, highlightbackground=t["border"],
                   command=command).grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 6, 0))
            options.grid_columnconfigure(col, weight=1)

        # color swatches + custom color
        Label(section, text="Color", font=self.App.adjust_font(10), bg=t["sidebar"], fg=t["text"]).pack(anchor="w", pady=(12, 4))
        colors = Frame(section, bg=t["sidebar"])
        colors.pack(anchor="w")
        for col, color in enumerate(BG_COLORS):
            swatch = Label(colors, bg=color, width=2, height=1, cursor="hand2",
                           highlightthickness=1, highlightbackground=t["border"])
            swatch.grid(row=0, column=col, padx=(0, 6))
            swatch.bind("<Button-1>", lambda e, c=color: self.ApplyBackground("color", c))
        Button(colors, text="+", font=self.App.adjust_font(10, bold=True), width=2,
               bg=t["accent_light"], fg=t["accent"], activebackground=t["trough"], activeforeground=t["accent"],
               relief=FLAT, bd=0, cursor="hand2", command=self.PickColor).grid(row=0, column=len(BG_COLORS))

        # ----- Tip -----
        section = self.Section(None)
        Label(section, text="Tip: save as PNG to keep a transparent background. JPG turns it white.",
              font=self.App.adjust_font(9), bg=t["sidebar"], fg=t["muted"],
              wraplength=self.App.scale_x(320), justify=LEFT).pack(anchor="w")

        # mouse on the image draws the box
        self.canvas.bind("<ButtonPress-1>", self.OnPress)
        self.canvas.bind("<B1-Motion>", self.OnDrag)
        self.canvas.config(cursor="crosshair")

        self.bind("<Destroy>", self.OnDestroy)

        # let the Editor find this panel (it calls DrawBox after redrawing the image)
        self.App.bg_panel = self

    def Section(self, title):
        # thin line, then (optional) title, then the section's content
        t = self.t
        Frame(self, bg=t["border"], height=1).pack(fill=X, padx=20, pady=(14, 0))
        section = Frame(self, bg=t["sidebar"])
        section.pack(fill=X, padx=20, pady=(12, 0))
        if title:
            Label(section, text=title, font=self.App.adjust_font(11, bold=True),
                  bg=t["sidebar"], fg=t["text"]).pack(anchor="w")
        return section

    # ---------------- Box ----------------

    def ToFraction(self, event):
        # mouse position -> position inside the image as 0 to 1 (kept inside the image)
        x = (self.canvas.canvasx(event.x) - self.Editor.image_x) / self.Editor.display_width
        y = (self.canvas.canvasy(event.y) - self.Editor.image_y) / self.Editor.display_height
        return min(max(x, 0), 1), min(max(y, 0), 1)

    def OnPress(self, event):
        if self.Editor.active_image is None:
            return
        self.start_x, self.start_y = self.ToFraction(event)
        self.box = None
        self.Status.config(text="")
        self.DrawBox()

    def OnDrag(self, event):
        if self.Editor.active_image is None:
            return
        x, y = self.ToFraction(event)
        self.box = [min(self.start_x, x), min(self.start_y, y), max(self.start_x, x), max(self.start_y, y)]
        self.DrawBox()

    def DrawBox(self):
        # the Editor calls this after redrawing the image
        self.canvas.delete("bg_box")
        if self.box is None or self.Editor.active_image is None:
            return
        left, top, right, bottom = self.box
        ix, iy = self.Editor.image_x, self.Editor.image_y
        iw, ih = self.Editor.display_width, self.Editor.display_height
        self.canvas.create_rectangle(ix + left * iw, iy + top * ih, ix + right * iw, iy + bottom * ih,
                                     outline="#7cf29c", width=2, dash=(6, 4), tags="bg_box")

    def ClearBox(self):
        self.box = None
        self.Status.config(text="")
        self.DrawBox()

    # ---------------- Remove ----------------

    def Remove(self):
        if self.Editor.active_image is None:
            return
        if self.box is None:
            self.Status.config(text="Draw a box around the subject first", fg=self.t["danger"])
            return

        # show the message before the (slow) work starts
        self.Status.config(text="Removing background...", fg=self.t["accent"])
        self.config(cursor="watch")
        self.update_idletasks()

        box = self.box
        self.box = None
        done = self.Editor.RemoveBackground(*box)

        self.config(cursor="")
        if done:
            self.Status.config(text="Done! Undo if you don't like it.", fg=self.t["accent"])
        else:
            self.box = box
            self.DrawBox()
            self.Status.config(text="Couldn't find the subject, try a bigger box", fg=self.t["danger"])

    # ---------------- New background ----------------

    def ApplyBackground(self, mode, color=None, image_path=None):
        if self.Editor.active_image is None:
            return
        color_bgr = None
        if color:
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            color_bgr = (b, g, r)                          # OpenCV order

        if self.Editor.SetBackground(mode, color_bgr=color_bgr, image_path=image_path):
            names = {"none": "Transparent", "blur": "Blurred photo", "image": "Your image"}
            name = color.upper() if mode == "color" else names[mode]
            self.Status.config(text=f"Background: {name}", fg=self.t["accent"])
        elif self.Editor.active_image.cutout is None:
            self.Status.config(text="Remove the background first", fg=self.t["danger"])
        else:
            self.Status.config(text="Couldn't open that image", fg=self.t["danger"])

    def PickColor(self):
        result = colorchooser.askcolor(title="Background color", parent=self)
        if result and result[1]:
            self.ApplyBackground("color", result[1])

    def PickImage(self):
        if self.Editor.active_image is None:
            return
        if self.Editor.active_image.cutout is None:
            self.Status.config(text="Remove the background first", fg=self.t["danger"])
            return
        path = filedialog.askopenfilename(title="Choose a background image", parent=self,
                                          filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")])
        if path:
            self.ApplyBackground("image", image_path=path)

    # ---------------- Closing ----------------

    def OnDestroy(self, event):
        if event.widget is not self:
            return
        try:
            self.canvas.delete("bg_box")
            self.canvas.unbind("<ButtonPress-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.config(cursor="")
        except TclError:
            pass   # canvas already gone (app closing)
        self.App.bg_panel = None