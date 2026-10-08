from tkinter import *


class BackgroundRemover(Frame):
    # Background Remover: draw a box around the subject, everything else becomes transparent
    def __init__(self, App, PanelFrame):
        self.t = App.theme                          # colors from main.py
        t = self.t
        super().__init__(PanelFrame, bg=t["sidebar"])
        self.App = App
        self.Editor = App.editor
        self.canvas = self.Editor.canvas

        self.method = StringVar(value="opencv")
        self.box = None            # [left, top, right, bottom] as fractions of the image, None = no box
        self.start_x = 0
        self.start_y = 0

        # ----- title -----
        Label(self, text="Remove Background", font=self.App.adjust_font(16, bold=True),
              bg=t["sidebar"], fg=t["accent"]).pack(anchor="w", padx=20, pady=(18, 0))
        Label(self, text="Keep the subject, make the rest transparent", font=self.App.adjust_font(10),
              bg=t["sidebar"], fg=t["muted"]).pack(anchor="w", padx=20, pady=(0, 6))

        # ----- Method -----
        section = self.Section("Method")
        self.App.CreateMethodPicker(section, self.method).pack(anchor="w", pady=(8, 0))

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

        # ----- Tip -----
        section = self.Section(None)
        Label(section, text="Tip: save as PNG to keep the transparent background. JPG turns it white/black.",
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