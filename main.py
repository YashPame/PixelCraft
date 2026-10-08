from tkinter import *
from tkinter import ttk

from Components.top_header import Header
from Components.editor_canvas import EditorCanvas

from Core.image_editor import Editor
from Components.action_bar import ActionBar

from Components.ui_icons_loader import UIIconsLoader
from Components.variables import Variables

DEFAULT_WIDTH = 1536
DEFAULT_HEIGHT = 864

# ---------------- THEME ----------------
# One place for every color / font used in the app.
THEME = {
    "font":          "Segoe UI",

    "app_bg":        "#e9ecf3",   # window background (around the canvas)
    "surface":       "#ffffff",   # header, toolbar, sidebar
    "surface_alt":   "#f3f5fa",   # button groups, buttons
    "border":        "#d7dce8",   # thin lines / outlines
    "canvas_bg":     "#262a35",   # dark workspace behind the photo

    "text":          "#1e2235",   # normal text
    "muted":         "#7c829a",   # hints, disabled text

    "accent":        "#2f3775",   # main color (same blue as the panel titles)
    "accent_hover":  "#232a5c",
    "accent_light":  "#e2e6f8",   # selected tool / hover

    "sidebar":       "#f2f3fb",   # side panel background (light lavender tint)
    "sidebar_text":  "#c9cdf0",   # small text on the blue sidebar header

    "danger":        "#d14b4b",   # cancel
    "trough":        "#d9ddeb",   # slider track
}

# ---------------- LAYOUT (in 1536 x 864 design pixels) ----------------
TOOLBAR_HEIGHT = 80
CANVAS = (208, 145, 1120, 700)            # x, y, width, height (centered, no panel)
CANVAS_X_WITH_PANEL = 16                  # canvas moves left when a panel is open
SIDEBAR_WIDTH = 370
SIDEBAR = (DEFAULT_WIDTH - SIDEBAR_WIDTH, 50 + TOOLBAR_HEIGHT, SIDEBAR_WIDTH, DEFAULT_HEIGHT - 50 - TOOLBAR_HEIGHT)


class PhotoEditorApp:
    def __init__(self, root):
        self.root = root
        self.theme = THEME
        self.CANVAS = CANVAS
        self.CANVAS_X_WITH_PANEL = CANVAS_X_WITH_PANEL
        self.SIDEBAR = SIDEBAR

        self.ratioW, self.ratioH = self.setRatio()
        self.root.geometry(f'{str(int(DEFAULT_WIDTH*self.ratioW))}x{str(int(DEFAULT_HEIGHT*self.ratioH))}+0+0')
        self.root.config(bd=0, bg=THEME["app_bg"])
        self.root.attributes('-fullscreen', True)

        self.ApplyTheme()

        self.ui_icon_loader = UIIconsLoader(self)
        self.variables = Variables(self)

        self.editor = None

        self.header = Header(self)
        self.place_component(self.header, 0, 0, DEFAULT_WIDTH, 46)

        self.canvas_frame = EditorCanvas(self)
        self.hasImage.trace_add("write", self.UpdateButtons)

        self.PanelsFrame = Frame(self.root, bg=THEME["surface"])

        self.action_bar = ActionBar(self)
        self.place_component(self.action_bar, 0, 50, DEFAULT_WIDTH, TOOLBAR_HEIGHT)

    def ApplyTheme(self):
        # Default colors for every widget (panels, dialogs, ...) unless a widget sets its own
        t = THEME
        r = self.root

        r.option_add("*Font", (t["font"], 10))
        r.option_add("*Background", t["surface"])
        r.option_add("*Foreground", t["text"])
        r.option_add("*activeBackground", t["accent_light"])
        r.option_add("*activeForeground", t["text"])
        r.option_add("*disabledForeground", t["muted"])
        r.option_add("*highlightBackground", t["surface"])
        r.option_add("*highlightColor", t["accent"])
        r.option_add("*selectBackground", t["accent"])
        r.option_add("*selectForeground", "#ffffff")

        r.option_add("*Button.Background", t["surface_alt"])
        r.option_add("*Button.relief", "flat")
        r.option_add("*Button.cursor", "hand2")
        r.option_add("*Entry.Background", t["surface_alt"])
        r.option_add("*Entry.relief", "flat")
        r.option_add("*Listbox.Background", t["surface_alt"])
        r.option_add("*Canvas.Background", t["canvas_bg"])
        r.option_add("*Canvas.highlightThickness", 0)
        r.option_add("*Scrollbar.troughColor", t["surface_alt"])

        # ttk widgets (sliders, combo boxes, ...)
        style = ttk.Style(r)
        style.theme_use("clam")
        style.configure(".", background=t["surface"], foreground=t["text"], font=(t["font"], 10))
        style.configure("Horizontal.TScale", background=t["accent"], troughcolor=t["trough"],
                        bordercolor=t["trough"], lightcolor=t["accent"], darkcolor=t["accent"])
        style.map("Horizontal.TScale", background=[("active", t["accent_hover"])])
        style.configure("TButton", background=t["surface_alt"], bordercolor=t["border"], padding=6)
        style.map("TButton", background=[("active", t["accent_light"])])
        style.configure("TCombobox", fieldbackground=t["surface_alt"], background=t["surface_alt"],
                        bordercolor=t["border"], arrowcolor=t["accent"])
        style.configure("Vertical.TScrollbar", background=t["surface_alt"], troughcolor=t["surface"],
                        bordercolor=t["surface"], arrowcolor=t["muted"])
        style.configure("Horizontal.TScrollbar", background=t["surface_alt"], troughcolor=t["surface"],
                        bordercolor=t["surface"], arrowcolor=t["muted"])

    def CreateSlider(self, parent, from_=-100, to=100, resolution=1, length=210, **kwargs):
        # Themed slider for all panels: thin light track, navy handle.
        # Use it like a normal slider: .set(), .get(), .config(command=...), .bind(...)
        t = THEME
        return Scale(parent, from_=from_, to=to, resolution=resolution, orient=HORIZONTAL,
                     length=self.scale_x(length), showvalue=0, width=8, sliderlength=18,
                     bd=0, highlightthickness=0, sliderrelief=FLAT,
                     bg=t["accent"], activebackground=t["accent_hover"], troughcolor=t["trough"],
                     cursor="hand2", **kwargs)

    def CreateMethodPicker(self, parent, variable):
        # Two toggle tiles: "OpenCV" (works now) and "AI" (coming soon, can't be picked yet)
        t = THEME
        frame = Frame(parent, bg=t["sidebar"])
        options = [("OpenCV", "opencv", NORMAL), ("AI  ·  Coming soon", "ai", DISABLED)]
        for col, (text, value, state) in enumerate(options):
            Radiobutton(frame, text=text, variable=variable, value=value, state=state,
                        indicatoron=0, font=self.adjust_font(10, bold=True), width=16, pady=6,
                        bg=t["surface"], fg=t["text"], selectcolor=t["accent_light"],
                        activebackground=t["accent_light"], activeforeground=t["accent"],
                        disabledforeground=t["muted"], relief=FLAT, offrelief=FLAT, bd=0, cursor="hand2",
                        highlightthickness=1, highlightbackground=t["border"]).grid(row=0, column=col, padx=(0, 8))
        return frame

    def UpdateButtons(self, *args):
        self.PanelsFrame.place_forget()
        if self.hasImage.get():
            self.place_component(self.canvas_frame, *CANVAS)
        else:
            self.canvas_frame.place_forget()

    def setRatio(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        ratioW = DEFAULT_WIDTH / screen_width
        ratioH = DEFAULT_HEIGHT / screen_height
        return ratioW, ratioH

    def place_component(self, widget, x, y, w, h, **kwargs):
        widget.place(x=int(x*self.ratioW), y=int(y*self.ratioH), w=int(w*self.ratioW), h=int(h*self.ratioH), **kwargs)

    def place_configure(self, widget, x, y):
        widget.place_configure(x=int(x*self.ratioW), y=int(y*self.ratioH))

    def scale_x(self, x):
        return int(x*self.ratioW)

    def scale_y(self, y):
        return int(y*self.ratioH)

    def adjust_font(self, font, font_name=THEME["font"], bold=False):
        # {} keeps names with spaces (like "Segoe UI") together
        fontstr = f"{{{font_name}}} {int(font*self.ratioH)}"
        if bold:
            fontstr += " bold"
        return fontstr


if __name__ == '__main__':
    root = Tk()
    obj = PhotoEditorApp(root)
    # root.overrideredirect(1)
    root.mainloop()