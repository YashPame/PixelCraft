from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from tkinter import filedialog
from Components.Panels.crop_panel import CropPanel
from Components.Panels.light_panel import LightPanel
from Components.Panels.drawing_panels import DrawingPanel
from Components.Panels.eraser_panel import EraserPanel
from Components.Panels.bgremover_panel import BackgroundRemover
from Components.Panels.filters_panel import FiltersPanel
from Components.save_dialog import SaveDialog


class ActionBar(Frame):
    def __init__(self, App):
        self.t = App.theme                                # colors from main.py
        super().__init__(App.root, bg=self.t["surface"])

        self.App = App
        self.Editor = self.App.editor
        self.PanelsFrame = None
        self.OpenImageFrame = None                       # center "Open Image" box
        self.zoom_placeholder = StringVar(value="100%")  # zoom text when no image

        # thin line under the toolbar
        Frame(self, bg=self.t["border"]).place(x=0, rely=1, relwidth=1, height=1, anchor="sw")

        self.CreateButtons()
        self.App.hasImage.trace_add("write", self.UpdateButtons)

    # ---------------- styles ----------------

    def ToolStyle(self):
        # icon buttons (tools, zoom, undo, redo)
        t = self.t
        return dict(bg=t["surface_alt"], activebackground=t["accent_light"], relief=FLAT, bd=0,
                    highlightthickness=0, cursor="hand2")

    def TextButtonStyle(self, size=11):
        t = self.t
        return dict(font=self.App.adjust_font(size, bold=True), fg=t["text"], disabledforeground=t["muted"],
                    **self.ToolStyle())

    def CreateButtons(self):
        t = self.t
        has_image = self.App.hasImage.get()
        state = NORMAL if has_image else DISABLED

        self.CoreTitleButtons = Frame(self, bg=t["surface"])
        self.CoreTitleButtons.place(x=0, y=0, relwidth=1, relheight=1, height=-1)

        # ---------------- top tool buttons (always shown, disabled without an image) ----------------
        tool = self.ToolStyle()
        self.crop_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Crop, state=state, command=lambda: self.TopButtonClicked("Crop"), **tool)
        self.brightness_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Brightenss, state=state, command=lambda: self.TopButtonClicked("Brightness"), **tool)
        # brush icon opens the Filters panel
        self.filters_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Brush, state=state, command=lambda: self.TopButtonClicked("Filters"), **tool)
        self.pencil_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Pencil, state=state, command=lambda: self.TopButtonClicked("Pencil"), **tool)
        self.eraser_button = Button(self.CoreTitleButtons, image=self.App.IconImage_Eraser, state=state, command=lambda: self.TopButtonClicked("Eraser"), **tool)
        self.background_remover_button = Button(self.CoreTitleButtons, image=self.App.IconImage_BackgroundRemover, state=state, command=lambda: self.TopButtonClicked("Background Remover"), **tool)

        self.App.place_component(self.crop_button, 1536/2-175, 15, 50, 50)
        self.App.place_component(self.brightness_button, 1536/2-115, 15, 50, 50)
        self.App.place_component(self.filters_button, 1536/2-55, 15, 50, 50)
        self.App.place_component(self.pencil_button, 1536/2+5, 15, 50, 50)
        self.App.place_component(self.eraser_button, 1536/2+65, 15, 50, 50)
        self.App.place_component(self.background_remover_button, 1536/2+125, 15, 50, 50)

        # ---------------- left: zoom / reset / undo / redo ----------------
        left_options_frame = Frame(self.CoreTitleButtons, bg=t["surface_alt"],
                                   highlightthickness=1, highlightbackground=t["border"])
        self.App.place_component(left_options_frame, 30, 15, 355, 50)

        if has_image and self.Editor.active_image is not None:
            zoom_var = self.Editor.active_image.zoom_percentage
        else:
            zoom_var = self.zoom_placeholder

        zoom_in_button = Button(left_options_frame, image=self.App.IconImage_ZoomIn, state=state, command=self.Editor.ZoomIn, **tool)
        zoom_out_button = Button(left_options_frame, image=self.App.IconImage_ZoomOut, state=state, command=self.Editor.ZoomOut, **tool)
        zoom_percentage_label = Label(left_options_frame, textvariable=zoom_var, font=self.App.adjust_font(11, bold=True),
                                      bg=t["surface_alt"], fg=t["text"], disabledforeground=t["muted"], state=state)
        seperator1 = Frame(left_options_frame, bg=t["border"])

        reset_button = Button(left_options_frame, text="Reset", state=state, command=self.Editor.Reset, **self.TextButtonStyle())
        undo_button = Button(left_options_frame, image=self.App.IconImage_Undo, state=state, command=self.Editor.Undo, **tool)
        redo_button = Button(left_options_frame, image=self.App.IconImage_Redo, state=state, command=self.Editor.Redo, **tool)

        self.App.place_component(zoom_in_button, 10, 9, 30, 30)
        self.App.place_component(zoom_out_button, 50, 9, 30, 30)
        self.App.place_component(zoom_percentage_label, 90, 9, 60, 30)
        self.App.place_component(seperator1, 160, 9, 1, 30)
        self.App.place_component(reset_button, 170, 9, 55, 30)
        self.App.place_component(undo_button, 235, 9, 50, 30)
        self.App.place_component(redo_button, 290, 9, 50, 30)

        # ---------------- right: save / cancel ----------------
        right_options_frame = Frame(self.CoreTitleButtons, bg=t["surface"])
        self.App.place_component(right_options_frame, 1536-240, 15, 210, 50)

        save_button = Button(right_options_frame, text="Save", font=self.App.adjust_font(12, bold=True),
                             bg=t["accent"], fg="#ffffff", activebackground=t["accent_hover"], activeforeground="#ffffff",
                             disabledforeground="#9aa0c8", relief=FLAT, bd=0, highlightthickness=0, cursor="hand2",
                             state=state, command=self.SaveClicked)
        cancel_button = Button(right_options_frame, text="Cancel", font=self.App.adjust_font(12, bold=True),
                               bg=t["surface"], fg=t["danger"], activebackground="#fbeaea", activeforeground=t["danger"],
                               disabledforeground=t["muted"], relief=FLAT, bd=0, cursor="hand2",
                               highlightthickness=1, highlightbackground=t["border"],
                               state=state, command=self.CancelClicked)

        self.App.place_component(save_button, 10, 5, 100, 40)
        self.App.place_component(cancel_button, 120, 5, 85, 40)

        # ---------------- center "Open Image" box (where the canvas will appear) ----------------
        if not has_image:
            self.CreateOpenImagePlaceholder()

    def CreateOpenImagePlaceholder(self):
        # Welcome screen shown where the image will appear: dotted background,
        # a dashed "open" card in the middle and the app's features listed below it
        t = self.t
        W, H = self.App.scale_x(self.App.CANVAS[2]), self.App.scale_y(self.App.CANVAS[3])

        self.OpenImageFrame = Canvas(self.App.root, bg=t["surface"], highlightthickness=1,
                                     highlightbackground=t["border"])
        self.App.place_component(self.OpenImageFrame, *self.App.CANVAS)
        c = self.OpenImageFrame

        # 1. soft dot grid in the background
        gap = self.App.scale_x(26)
        for x in range(gap // 2, W, gap):
            for y in range(gap // 2, H, gap):
                c.create_oval(x - 1, y - 1, x + 1, y + 1, fill=t["border"], outline="")

        # 2. dashed card in the middle (click anywhere on it to open an image)
        cw, ch = self.App.scale_x(500), self.App.scale_y(290)
        x1, y1 = (W - cw) // 2, (H - ch) // 2 - self.App.scale_y(30)
        c.create_rectangle(x1, y1, x1 + cw, y1 + ch, fill=t["sidebar"], outline=t["accent"],
                           width=2, dash=(8, 6), tags=("card", "card_bg"))

        open_img_button = Button(c, image=self.App.IconImage_OpenFile, bg=t["accent_light"],
                                 activebackground=t["trough"], relief=FLAT, bd=0, highlightthickness=0,
                                 cursor="hand2", command=self.Editor.OpenImage)
        c.create_window(W // 2, y1 + ch * 0.36, window=open_img_button, width=self.App.scale_x(84), height=self.App.scale_y(84))

        c.create_text(W // 2, y1 + ch * 0.66, text="Open an Image", font=self.App.adjust_font(18, bold=True),
                      fill=t["accent"], tags="card")
        c.create_text(W // 2, y1 + ch * 0.80, text="Click here to choose a JPG or PNG from your computer",
                      font=self.App.adjust_font(11), fill=t["muted"], tags="card")

        # hover: card gets a little darker, click opens the file dialog
        c.tag_bind("card", "<Enter>", lambda e: (c.itemconfig("card_bg", fill=t["accent_light"]), c.config(cursor="hand2")))
        c.tag_bind("card", "<Leave>", lambda e: (c.itemconfig("card_bg", fill=t["sidebar"]), c.config(cursor="")))
        c.tag_bind("card", "<Button-1>", lambda e: self.Editor.OpenImage())

        # 3. what you can do, as small chips under the card
        features = ["Crop & Rotate", "Light & Color", "Filters", "Draw", "Magic Eraser", "Remove Background"]
        chip_y = y1 + ch + self.App.scale_y(55)
        pad_x, pad_y, space = self.App.scale_x(12), self.App.scale_y(6), self.App.scale_x(10)

        c.create_text(W // 2, chip_y - self.App.scale_y(32), text="WHAT YOU CAN DO",
                      font=self.App.adjust_font(9, bold=True), fill=t["muted"])

        texts = [c.create_text(0, chip_y, text=name, font=self.App.adjust_font(10, bold=True), fill=t["accent"], anchor="w")
                 for name in features]
        widths = [c.bbox(item)[2] - c.bbox(item)[0] for item in texts]
        x = (W - (sum(widths) + len(widths) * 2 * pad_x + (len(widths) - 1) * space)) // 2

        for item, width in zip(texts, widths):
            c.move(item, x + pad_x, 0)
            _, top, _, bottom = c.bbox(item)
            chip = c.create_rectangle(x, top - pad_y, x + width + 2 * pad_x, bottom + pad_y,
                                      fill=t["accent_light"], outline="")
            c.tag_lower(chip, item)
            x += width + 2 * pad_x + space

    def GetButtons(self):
        # top buttons by name
        return {
            "Crop": self.crop_button,
            "Brightness": self.brightness_button,
            "Filters": self.filters_button,
            "Pencil": self.pencil_button,
            "Eraser": self.eraser_button,
            "Background Remover": self.background_remover_button
        }

    def ClosePanel(self):
        # un-highlight the active button, remove the side panel, center the canvas
        current_button = self.App.activeTopButton.get()

        if current_button != "None":
            self.GetButtons()[current_button].config(bg=self.t["surface_alt"])
            self.App.activeTopButton.set("None")

        if self.PanelsFrame:
            self.PanelsFrame.destroy()
            self.PanelsFrame = None

        self.App.place_configure(self.App.canvas_frame, self.App.CANVAS[0], self.App.CANVAS[1])

    def TopButtonClicked(self, button_name):
        t = self.t
        current_button = self.App.activeTopButton.get()
        buttons = self.GetButtons()

        # clicking the active button again closes its panel
        if current_button == button_name:
            self.ClosePanel()
            return

        if current_button != "None":
            buttons[current_button].config(bg=t["surface_alt"])

        buttons[button_name].config(bg=t["accent_light"])

        if self.PanelsFrame:
            self.PanelsFrame.destroy()

        self.App.place_configure(self.App.canvas_frame, self.App.CANVAS_X_WITH_PANEL, self.App.CANVAS[1])

        # sidebar on the right edge, a different shade from the background + accent strip
        self.PanelsFrame = Frame(self.App.root, bg=t["sidebar"], highlightthickness=1, highlightbackground=t["border"])
        self.App.place_component(self.PanelsFrame, *self.App.SIDEBAR)
        # Frame(self.PanelsFrame, bg=t["accent"], width=4).pack(side=LEFT, fill=Y)

        if button_name == "Crop":
            self.Panel = CropPanel(self.App, self.PanelsFrame)
        elif button_name == "Brightness":
            self.Panel = LightPanel(self.App, self.PanelsFrame)
        elif button_name == "Filters":
            self.Panel = FiltersPanel(self.App, self.PanelsFrame)
        elif button_name == "Pencil":
            self.Panel = DrawingPanel(self.App, self.PanelsFrame)
        elif button_name == "Eraser":
            self.Panel = EraserPanel(self.App, self.PanelsFrame)
        elif button_name == "Background Remover":
            self.Panel = BackgroundRemover(self.App, self.PanelsFrame)
        self.Panel.pack(fill=BOTH, expand=True)

        self.App.activeTopButton.set(button_name)

    def SaveClicked(self):
        if self.Editor.active_image is None:
            return
        SaveDialog(self.App)

    def CancelClicked(self):
        doc = self.Editor.active_image
        if doc is None:
            return

        if doc.modified:
            answer = messagebox.askyesno(
                "Discard changes?",
                "You have unsaved changes.\nDo you want to discard them and go back?"
            )
            if not answer:
                return

        self.ClosePanel()          # close the side panel first (it uses the canvas)
        self.Editor.CloseImage()   # then remove the image -> back to Open Image screen

    def UpdateButtons(self, *args):
        # rebuild the toolbar whenever hasImage changes
        self.CoreTitleButtons.destroy()
        if self.OpenImageFrame:
            self.OpenImageFrame.destroy()
            self.OpenImageFrame = None
        self.CreateButtons()