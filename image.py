import os
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk
import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageTk

MODEL_PATH = r"C:\Users\Acer\Downloads\lama_fp32.onnx"


class ImageEditorApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Image Studio + ONNX Magic Eraser")
        self.root.geometry("1300x850")
        self.root.minsize(1000, 650)

        # Core State
        self.original_image = None
        self.base_image = None
        self.preview_image = None
        self.active_filter = None

        # ONNX Engine Session
        self.onnx_session = None

        # Masking / Canvas State
        self.eraser_mask = None
        self.brush_size = 25
        self.tk_image = None
        self.filter_thumbnails = {}

        # Drawing Tool State
        self.drawing_layer = None
        self.draw_tool = "pen"  # 'pen', 'pencil', 'eraser'
        self.draw_color = "#FF0000"  # Hex color string
        self.draw_brush_size = 8
        self.last_draw_point = None

        # Crop State
        self.crop_start_x = None
        self.crop_start_y = None
        self.crop_rect = None
        self.crop_mode = False

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

    def _build_ui(self):
        top_bar = ttk.Frame(self.root, padding="5")
        top_bar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(top_bar, text="📁 Open Image", command=self.load_image).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            top_bar, text="💾 Save / Convert", command=self.save_image
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            top_bar, text="↩ Reset to Original", command=self.reset_to_original
        ).pack(side=tk.LEFT, padx=5)

        workspace = ttk.Frame(self.root)
        workspace.pack(expand=True, fill=tk.BOTH)

        self.notebook = ttk.Notebook(workspace, width=380)
        self.notebook.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        self.tab_adjust = ttk.Frame(self.notebook, padding="10")
        self.tab_filters = ttk.Frame(self.notebook, padding="10")
        self.tab_eraser = ttk.Frame(self.notebook, padding="10")
        self.tab_draw = ttk.Frame(self.notebook, padding="10")
        self.tab_bg = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.tab_adjust, text=" Adjust & Crop ")
        self.notebook.add(self.tab_filters, text=" Filters ")
        self.notebook.add(self.tab_eraser, text=" 🪄 Magic Eraser ")
        self.notebook.add(self.tab_draw, text=" 🎨 Draw ")
        self.notebook.add(self.tab_bg, text=" 🖼️ Background ")

        self.canvas_frame = ttk.Frame(workspace, padding="5")
        self.canvas_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#1e1e1e")
        self.canvas.pack(expand=True, fill=tk.BOTH)

        self._build_adjust_tab()
        self._build_filters_tab()
        self._build_eraser_tab()
        self._build_draw_tab()
        self._build_bg_tab()

        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    # --- ADJUST TAB ---
    def _build_adjust_tab(self):
        rot_group = ttk.LabelFrame(
            self.tab_adjust, text="Rotation (°)", padding="5"
        )
        rot_group.pack(fill=tk.X, pady=5)

        self.rot_val_label = ttk.Label(rot_group, text="0°")
        self.rot_val_label.pack(anchor=tk.E)

        self.rotation_slider = ttk.Scale(
            rot_group,
            from_=-180,
            to=180,
            value=0,
            command=self.update_live_preview,
        )
        self.rotation_slider.pack(fill=tk.X, pady=2)

        transform_group = ttk.LabelFrame(
            self.tab_adjust, text="Flips & Crop", padding="5"
        )
        transform_group.pack(fill=tk.X, pady=5)

        f_grid = ttk.Frame(transform_group)
        f_grid.pack(fill=tk.X, pady=2)
        ttk.Button(
            f_grid, text="Flip Horiz", command=lambda: self.flip_image("H")
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(
            f_grid, text="Flip Vert", command=lambda: self.flip_image("V")
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        self.crop_btn = ttk.Button(
            transform_group,
            text="Enable Crop Tool",
            command=self.toggle_crop_mode,
        )
        self.crop_btn.pack(fill=tk.X, pady=4)

        resize_group = ttk.LabelFrame(
            self.tab_adjust, text="Resize (Px)", padding="5"
        )
        resize_group.pack(fill=tk.X, pady=5)

        res_f = ttk.Frame(resize_group)
        res_f.pack(fill=tk.X)
        self.w_entry = ttk.Entry(res_f, width=6)
        self.w_entry.pack(side=tk.LEFT, padx=2)
        ttk.Label(res_f, text="x").pack(side=tk.LEFT)
        self.h_entry = ttk.Entry(res_f, width=6)
        self.h_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(res_f, text="Resize", command=self.apply_resize).pack(
            side=tk.LEFT, padx=4
        )

        adj_group = ttk.LabelFrame(
            self.tab_adjust, text="Enhancements", padding="5"
        )
        adj_group.pack(fill=tk.X, pady=5)

        ttk.Label(adj_group, text="Brightness").pack(anchor=tk.W)
        self.bright_slider = ttk.Scale(
            adj_group,
            from_=0.2,
            to=2.0,
            value=1.0,
            command=self.update_live_preview,
        )
        self.bright_slider.pack(fill=tk.X, pady=2)

        ttk.Label(adj_group, text="Contrast").pack(anchor=tk.W)
        self.contrast_slider = ttk.Scale(
            adj_group,
            from_=0.2,
            to=2.0,
            value=1.0,
            command=self.update_live_preview,
        )
        self.contrast_slider.pack(fill=tk.X, pady=2)

        ttk.Label(adj_group, text="Sharpness").pack(anchor=tk.W)
        self.sharp_slider = ttk.Scale(
            adj_group,
            from_=0.0,
            to=3.0,
            value=1.0,
            command=self.update_live_preview,
        )
        self.sharp_slider.pack(fill=tk.X, pady=2)

        act_frame = ttk.Frame(self.tab_adjust)
        act_frame.pack(fill=tk.X, pady=10)
        ttk.Button(
            act_frame, text="✅ Apply Adjustments", command=self.commit_changes
        ).pack(fill=tk.X, pady=2)
        ttk.Button(
            act_frame,
            text="❌ Discard Adjustments",
            command=self.discard_adjustments,
        ).pack(fill=tk.X, pady=2)

    # --- FILTERS TAB ---
    def _build_filters_tab(self):
        info_label = ttk.Label(
            self.tab_filters,
            text="Click a preview thumbnail to sample a filter on the canvas.",
            wraplength=320,
        )
        info_label.pack(anchor=tk.W, pady=5)

        gallery_canvas = tk.Canvas(self.tab_filters, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self.tab_filters, orient="vertical", command=gallery_canvas.yview
        )
        self.gallery_frame = ttk.Frame(gallery_canvas)

        self.gallery_frame.bind(
            "<Configure>",
            lambda e: gallery_canvas.configure(
                scrollregion=gallery_canvas.bbox("all")
            ),
        )
        gallery_canvas.create_window(
            (0, 0), window=self.gallery_frame, anchor="nw"
        )
        gallery_canvas.configure(yscrollcommand=scrollbar.set)

        gallery_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        filter_act_frame = ttk.Frame(self.tab_filters)
        filter_act_frame.pack(
            side=tk.BOTTOM, fill=tk.X, pady=10, before=gallery_canvas
        )

        ttk.Button(
            filter_act_frame,
            text="✅ Apply Selected Filter",
            command=self.commit_changes,
        ).pack(fill=tk.X, pady=2)
        ttk.Button(
            filter_act_frame,
            text="🚫 Remove / Cancel Filter",
            command=self.remove_filter,
        ).pack(fill=tk.X, pady=2)

    # --- MAGIC ERASER TAB ---
    def _build_eraser_tab(self):
        info_label = ttk.Label(
            self.tab_eraser,
            text="Paint red over any object you want to erase, then click 'Run ONNX Magic Eraser'.",
            wraplength=320,
        )
        info_label.pack(anchor=tk.W, pady=5)

        brush_group = ttk.LabelFrame(
            self.tab_eraser, text="Brush Settings", padding="5"
        )
        brush_group.pack(fill=tk.X, pady=5)

        ttk.Label(brush_group, text="Brush Radius (px):").pack(anchor=tk.W)
        self.brush_slider = ttk.Scale(
            brush_group,
            from_=5,
            to=80,
            value=self.brush_size,
            command=self._on_brush_slider_change,
        )
        self.brush_slider.pack(fill=tk.X, pady=2)

        self.brush_size_label = ttk.Label(
            brush_group, text=f"Radius: {self.brush_size}px"
        )
        self.brush_size_label.pack(anchor=tk.E)

        eraser_act = ttk.Frame(self.tab_eraser)
        eraser_act.pack(fill=tk.X, pady=15)

        self.erase_btn = ttk.Button(
            eraser_act,
            text="🪄 Run ONNX Magic Eraser",
            command=self.run_onnx_inpainting,
        )
        self.erase_btn.pack(fill=tk.X, pady=4)

        ttk.Button(
            eraser_act, text="🧹 Clear Selection Mask", command=self.clear_mask
        ).pack(fill=tk.X, pady=4)

        self.status_label = ttk.Label(
            self.tab_eraser,
            text="Ready.",
            font=("Helvetica", 9, "italic"),
            foreground="gray",
        )
        self.status_label.pack(anchor=tk.W, pady=10)

    # --- DRAWING STUDIO TAB ---
    def _build_draw_tab(self):
        tool_group = ttk.LabelFrame(
            self.tab_draw, text="Drawing Tools", padding="5"
        )
        tool_group.pack(fill=tk.X, pady=5)

        self.tool_var = tk.StringVar(value="pen")

        ttk.Radiobutton(
            tool_group,
            text="🖋️ Pen (Solid)",
            variable=self.tool_var,
            value="pen",
            command=self._on_draw_tool_change,
        ).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(
            tool_group,
            text="✏️ Pencil (Textured)",
            variable=self.tool_var,
            value="pencil",
            command=self._on_draw_tool_change,
        ).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(
            tool_group,
            text="🧹 Eraser",
            variable=self.tool_var,
            value="eraser",
            command=self._on_draw_tool_change,
        ).pack(anchor=tk.W, pady=2)

        color_group = ttk.LabelFrame(
            self.tab_draw, text="Brush Color", padding="5"
        )
        color_group.pack(fill=tk.X, pady=5)

        palette_frame = ttk.Frame(color_group)
        palette_frame.pack(fill=tk.X, pady=2)

        colors = ["#000000", "#FF0000", "#00FF00", "#0000FF", "#FFFFFF"]
        for c in colors:
            btn = tk.Button(
                palette_frame,
                bg=c,
                width=3,
                relief="groove",
                command=lambda col=c: self._set_draw_color(col),
            )
            btn.pack(side=tk.LEFT, padx=2)

        self.color_preview_btn = tk.Button(
            color_group,
            text="Custom Color...",
            bg=self.draw_color,
            command=self.choose_custom_color,
        )
        self.color_preview_btn.pack(fill=tk.X, pady=4)

        brush_group = ttk.LabelFrame(
            self.tab_draw, text="Brush Size", padding="5"
        )
        brush_group.pack(fill=tk.X, pady=5)

        self.draw_size_slider = ttk.Scale(
            brush_group,
            from_=1,
            to=50,
            value=self.draw_brush_size,
            command=self._on_draw_size_change,
        )
        self.draw_size_slider.pack(fill=tk.X, pady=2)

        self.draw_size_label = ttk.Label(
            brush_group, text=f"Size: {self.draw_brush_size}px"
        )
        self.draw_size_label.pack(anchor=tk.E)

        draw_act = ttk.Frame(self.tab_draw)
        draw_act.pack(fill=tk.X, pady=15)

        ttk.Button(
            draw_act,
            text="✅ Apply Drawing to Image",
            command=self.commit_drawing,
        ).pack(fill=tk.X, pady=4)
        ttk.Button(
            draw_act,
            text="🗑️ Clear Drawing Layer",
            command=self.clear_drawing_layer,
        ).pack(fill=tk.X, pady=4)

    # --- BACKGROUND CHANGER TAB ---
    def _build_bg_tab(self):
        info_label = ttk.Label(
            self.tab_bg,
            text="Select a solid, studio, or custom background to replace the image background.",
            wraplength=320,
        )
        info_label.pack(anchor=tk.W, pady=5)

        bg_group = ttk.LabelFrame(
            self.tab_bg, text="Preset Backgrounds", padding="5"
        )
        bg_group.pack(fill=tk.X, pady=5)

        bg_options = [
            ("Pure White", "#FFFFFF"),
            ("Dark Slate", "#1A1A1A"),
            ("Studio Light Grey", "#E0E0E0"),
            ("Cyberpunk Blue", "#002B45"),
            ("Sunset Red", "#4A0E17"),
            ("Emerald Green", "#0E3B27"),
        ]

        for label, hex_col in bg_options:
            btn = ttk.Button(
                bg_group,
                text=label,
                command=lambda c=hex_col: self.apply_preset_background(c),
            )
            btn.pack(fill=tk.X, pady=2)

        custom_group = ttk.LabelFrame(
            self.tab_bg, text="Custom Image Background", padding="5"
        )
        custom_group.pack(fill=tk.X, pady=5)

        ttk.Button(
            custom_group,
            text="🖼️ Choose Image Background...",
            command=self.apply_custom_image_background,
        ).pack(fill=tk.X, pady=4)

    # --- DRAWING TAB LOGIC ---
    def _on_draw_tool_change(self):
        self.draw_tool = self.tool_var.get()

    def _set_draw_color(self, hex_color):
        self.draw_color = hex_color
        self.color_preview_btn.config(bg=hex_color)

    def choose_custom_color(self):
        color = colorchooser.askcolor(
            color=self.draw_color, title="Select Brush Color"
        )
        if color[1]:
            self._set_draw_color(color[1])

    def _on_draw_size_change(self, val):
        self.draw_brush_size = int(float(val))
        self.draw_size_label.config(text=f"Size: {self.draw_brush_size}px")

    def _ensure_drawing_layer(self):
        if self.base_image and (
            self.drawing_layer is None
            or self.drawing_layer.size != self.base_image.size
        ):
            self.drawing_layer = Image.new(
                "RGBA", self.base_image.size, (0, 0, 0, 0)
            )

    def clear_drawing_layer(self):
        if self.base_image:
            self.drawing_layer = Image.new(
                "RGBA", self.base_image.size, (0, 0, 0, 0)
            )
            self.update_live_preview()

    def commit_drawing(self):
        if self.base_image and self.drawing_layer:
            composite = Image.alpha_composite(
                self.base_image.convert("RGBA"), self.drawing_layer
            )
            self.base_image = composite.convert("RGB")
            self.clear_drawing_layer()
            self.update_live_preview()
            messagebox.showinfo("Success", "Drawing applied to image!")

    def _paint_drawing_stroke(self, event):
        if self.base_image is None:
            return

        self._ensure_drawing_layer()
        draw = ImageDraw.Draw(self.drawing_layer)

        scale_x = self.base_image.width / self.preview_w
        scale_y = self.base_image.height / self.preview_h

        img_x = int((event.x - self.offset_x) * scale_x)
        img_y = int((event.y - self.offset_y) * scale_y)

        if self.last_draw_point is None:
            self.last_draw_point = (img_x, img_y)

        r = int(self.draw_brush_size * scale_x)

        if self.draw_tool == "eraser":
            # Clear alpha channel in drawing layer
            mask_draw = ImageDraw.Draw(self.drawing_layer)
            mask_draw.line(
                [self.last_draw_point, (img_x, img_y)],
                fill=(0, 0, 0, 0),
                width=r * 2,
            )
            mask_draw.ellipse(
                [img_x - r, img_y - r, img_x + r, img_y + r], fill=(0, 0, 0, 0)
            )
        else:
            color = self.draw_color
            if self.draw_tool == "pencil":
                # Give slight translucency for pencil effect
                rgb = tuple(
                    int(color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
                )
                fill_color = rgb + (180,)
            else:
                fill_color = color

            draw.line(
                [self.last_draw_point, (img_x, img_y)],
                fill=fill_color,
                width=r,
            )
            draw.ellipse(
                [img_x - r, img_y - r, img_x + r, img_y + r], fill=fill_color
            )

        self.last_draw_point = (img_x, img_y)
        self.update_live_preview()

    # --- BACKGROUND CHANGER LOGIC ---
    def _extract_foreground_mask(self, image_pil):
        """Generates a foreground mask using OpenCV GrabCut."""
        img_np = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
        h, w = img_np.shape[:2]

        mask = np.zeros((h, w), np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        # Margin crop for initial foreground estimate
        margin = int(min(h, w) * 0.05)
        rect = (margin, margin, w - (2 * margin), h - (2 * margin))

        cv2.grabCut(
            img_np,
            mask,
            rect,
            bgd_model,
            fgd_model,
            3,
            cv2.GC_INIT_WITH_RECT,
        )
        binary_mask = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8")

        # Smooth edges
        binary_mask = cv2.GaussianBlur(binary_mask * 255, (5, 5), 0) / 255.0
        return binary_mask

    def apply_preset_background(self, hex_color):
        if self.base_image is None:
            messagebox.showwarning("Warning", "Please open an image first!")
            return

        fg_mask = self._extract_foreground_mask(self.base_image)
        bg_color = tuple(
            int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
        )

        bg_pil = Image.new("RGB", self.base_image.size, bg_color)
        self._composite_background(bg_pil, fg_mask)

    def apply_custom_image_background(self):
        if self.base_image is None:
            messagebox.showwarning("Warning", "Please open an image first!")
            return

        bg_path = filedialog.askopenfilename(
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.bmp *.webp *.gif")
            ]
        )
        if bg_path:
            bg_pil = (
                Image.open(bg_path)
                .convert("RGB")
                .resize(self.base_image.size, Image.Resampling.LANCZOS)
            )
            fg_mask = self._extract_foreground_mask(self.base_image)
            self._composite_background(bg_pil, fg_mask)

    def _composite_background(self, bg_pil, fg_mask):
        fg_np = np.array(self.base_image, dtype=np.float32)
        bg_np = np.array(bg_pil, dtype=np.float32)

        alpha = fg_mask[:, :, np.newaxis]
        composite = (fg_np * alpha) + (bg_np * (1.0 - alpha))
        composite = np.clip(composite, 0, 255).astype(np.uint8)

        self.base_image = Image.fromarray(composite)
        self.update_live_preview()
        messagebox.showinfo("Success", "Background replaced!")

    # --- GENERAL APP & CANVAS LOGIC ---
    def _on_brush_slider_change(self, val):
        self.brush_size = int(float(val))
        self.brush_size_label.config(text=f"Radius: {self.brush_size}px")

    def run_onnx_inpainting(self):
        if self.base_image is None:
            messagebox.showwarning("Warning", "Please open an image first!")
            return

        if self.eraser_mask is None or np.max(self.eraser_mask) == 0:
            messagebox.showwarning(
                "Warning", "No object masked! Paint over an area first."
            )
            return

        if not os.path.exists(MODEL_PATH):
            messagebox.showerror(
                "Model Not Found",
                f"Could not find model file at:\n{MODEL_PATH}\n\nPlease verify the file location.",
            )
            return

        self._execute_onnx_inference()

    def _execute_onnx_inference(self):
        self.status_label.config(text="Processing AI Inpainting...")
        self.root.update()

        try:
            if self.onnx_session is None:
                self.onnx_session = ort.InferenceSession(
                    MODEL_PATH, providers=["CPUExecutionProvider"]
                )

            orig_w, orig_h = self.base_image.width, self.base_image.height

            img_resized = self.base_image.convert("RGB").resize(
                (512, 512), Image.Resampling.LANCZOS
            )
            mask_resized = cv2.resize(
                self.eraser_mask, (512, 512), interpolation=cv2.INTER_NEAREST
            )

            img_np = np.array(img_resized, dtype=np.float32) / 255.0
            mask_np = (mask_resized > 0).astype(np.float32)

            img_input = np.transpose(img_np, (2, 0, 1))[np.newaxis, ...]
            mask_input = mask_np[np.newaxis, np.newaxis, ...]

            input_names = [inp.name for inp in self.onnx_session.get_inputs()]
            inputs = {
                input_names[0]: img_input,
                input_names[1]: mask_input,
            }

            output = self.onnx_session.run(None, inputs)[0]

            out_img = output[0]
            if out_img.shape[0] in [1, 3]:
                out_img = np.transpose(out_img, (1, 2, 0))

            if out_img.max() <= 1.0:
                out_img = out_img * 255.0

            out_img = np.clip(out_img, 0, 255).astype(np.uint8)

            result_pil = Image.fromarray(out_img).resize(
                (orig_w, orig_h), Image.Resampling.LANCZOS
            )

            self.base_image = result_pil
            self.preview_image = self.base_image.copy()
            self.eraser_mask = np.zeros(
                (self.base_image.height, self.base_image.width), dtype=np.uint8
            )

            self.display_image(self.base_image)
            self.populate_filter_gallery()

            self.status_label.config(text="Object erased successfully!")
            messagebox.showinfo("Success", "Object seamlessly removed!")
        except Exception as e:
            messagebox.showerror(
                "Inpainting Error", f"Inference failed:\n{e}"
            )
            self.status_label.config(text="Inpainting error.")

    def clear_mask(self):
        if self.base_image:
            self.eraser_mask = np.zeros(
                (self.base_image.height, self.base_image.width), dtype=np.uint8
            )
            self.display_image(self.preview_image or self.base_image)
            self.status_label.config(text="Mask cleared.")

    def display_image(self, img):
        if img is None:
            return

        c_w = max(self.canvas.winfo_width(), 400)
        c_h = max(self.canvas.winfo_height(), 400)

        preview = img.copy()
        preview.thumbnail((c_w, c_h), Image.Resampling.LANCZOS)

        self.tk_image = ImageTk.PhotoImage(preview)
        self.canvas.delete("all")
        self.canvas.create_image(
            c_w // 2, c_h // 2, anchor=tk.CENTER, image=self.tk_image
        )

        self.preview_w, self.preview_h = preview.size
        self.offset_x = (c_w - self.preview_w) // 2
        self.offset_y = (c_h - self.preview_h) // 2

    def get_active_tab_title(self):
        return self.notebook.tab(self.notebook.select(), "text").strip()

    def on_canvas_press(self, event):
        active_tab = self.get_active_tab_title()
        if "Magic Eraser" in active_tab:
            self._paint_mask_stroke(event)
        elif "Draw" in active_tab:
            self.last_draw_point = None
            self._paint_drawing_stroke(event)
        elif self.crop_mode:
            self.on_crop_press(event)

    def on_canvas_drag(self, event):
        active_tab = self.get_active_tab_title()
        if "Magic Eraser" in active_tab:
            self._paint_mask_stroke(event)
        elif "Draw" in active_tab:
            self._paint_drawing_stroke(event)
        elif self.crop_mode:
            self.on_crop_drag(event)

    def on_canvas_release(self, event):
        active_tab = self.get_active_tab_title()
        if "Draw" in active_tab:
            self.last_draw_point = None
        elif self.crop_mode and "Magic Eraser" not in active_tab:
            self.on_crop_release(event)

    def _paint_mask_stroke(self, event):
        if self.base_image is None or self.eraser_mask is None:
            return

        scale_x = self.base_image.width / self.preview_w
        scale_y = self.base_image.height / self.preview_h

        img_x = int((event.x - self.offset_x) * scale_x)
        img_y = int((event.y - self.offset_y) * scale_y)

        r = self.brush_size // 2
        self.canvas.create_oval(
            event.x - r,
            event.y - r,
            event.x + r,
            event.y + r,
            fill="red",
            outline="red",
        )

        if 0 <= img_x < self.base_image.width and 0 <= img_y < self.base_image.height:
            cv2.circle(
                self.eraser_mask,
                (img_x, img_y),
                int(self.brush_size * scale_x),
                255,
                -1,
            )

    def update_live_preview(self, _=None):
        if self.base_image is None:
            return

        deg = int(self.rotation_slider.get())
        self.rot_val_label.config(text=f"{deg}°")

        img = self.base_image.copy()

        if deg != 0:
            img = img.rotate(
                deg, expand=True, resample=Image.Resampling.BICUBIC
            )

        b = self.bright_slider.get()
        if b != 1.0:
            img = ImageEnhance.Brightness(img).enhance(b)

        c = self.contrast_slider.get()
        if c != 1.0:
            img = ImageEnhance.Contrast(img).enhance(c)

        s = self.sharp_slider.get()
        if s != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(s)

        if self.active_filter:
            img = self._get_filtered_image(img, self.active_filter)

        if (
            self.drawing_layer
            and self.drawing_layer.size == self.base_image.size
        ):
            img = Image.alpha_composite(
                img.convert("RGBA"), self.drawing_layer
            ).convert("RGB")

        self.preview_image = img
        self.display_image(self.preview_image)

    def _get_filtered_image(self, img, filter_key):
        if filter_key == "BW":
            return img.convert("L").convert("RGB")
        elif filter_key == "BLUR":
            return img.filter(ImageFilter.GaussianBlur(radius=3))
        elif filter_key == "CONTOUR":
            return img.filter(ImageFilter.CONTOUR)
        elif filter_key == "EMBOSS":
            return img.filter(ImageFilter.EMBOSS)
        elif filter_key == "SHARPEN":
            return img.filter(ImageFilter.SHARPEN)
        elif filter_key == "EDGE":
            return img.filter(ImageFilter.FIND_EDGES)
        elif filter_key == "DETAIL":
            return img.filter(ImageFilter.DETAIL)
        return img

    def populate_filter_gallery(self):
        for widget in self.gallery_frame.winfo_children():
            widget.destroy()

        if self.base_image is None:
            return

        thumb_base = self.base_image.copy()
        thumb_base.thumbnail((80, 80), Image.Resampling.LANCZOS)

        filters = [
            ("Original / None", "NONE"),
            ("Black & White", "BW"),
            ("Soft Blur", "BLUR"),
            ("Contour", "CONTOUR"),
            ("Emboss", "EMBOSS"),
            ("Sharpen", "SHARPEN"),
            ("Find Edges", "EDGE"),
            ("Detail Boost", "DETAIL"),
        ]

        self.filter_thumbnails.clear()

        for idx, (label, key) in enumerate(filters):
            card = ttk.Frame(self.gallery_frame, padding="5")
            card.grid(
                row=idx // 2, column=idx % 2, padx=5, pady=5, sticky="nsew"
            )

            filtered_thumb = self._get_filtered_image(thumb_base, key)
            tk_thumb = ImageTk.PhotoImage(filtered_thumb)
            self.filter_thumbnails[key] = tk_thumb

            btn = tk.Button(
                card,
                image=tk_thumb,
                command=lambda k=key: self.select_filter(k),
                bd=1,
                relief="ridge",
            )
            btn.pack()

            lbl = ttk.Label(card, text=label, font=("Helvetica", 8))
            lbl.pack(pady=2)

    def select_filter(self, filter_key):
        self.active_filter = None if filter_key == "NONE" else filter_key
        self.update_live_preview()

    def remove_filter(self):
        self.active_filter = None
        self.update_live_preview()

    def commit_changes(self):
        if self.preview_image:
            self.base_image = self.preview_image.copy()
            self.active_filter = None
            self.reset_sliders_ui()

            self.eraser_mask = np.zeros(
                (self.base_image.height, self.base_image.width), dtype=np.uint8
            )

            self.w_entry.delete(0, tk.END)
            self.w_entry.insert(0, str(self.base_image.width))
            self.h_entry.delete(0, tk.END)
            self.h_entry.insert(0, str(self.base_image.height))

            self.populate_filter_gallery()
            self.display_image(self.base_image)
            messagebox.showinfo("Success", "Changes applied!")

    def discard_adjustments(self):
        self.reset_sliders_ui()
        self.active_filter = None
        self.update_live_preview()

    def reset_sliders_ui(self):
        self.rotation_slider.set(0)
        self.rot_val_label.config(text="0°")
        self.bright_slider.set(1.0)
        self.contrast_slider.set(1.0)
        self.sharp_slider.set(1.0)

    def load_image(self):
        f_path = filedialog.askopenfilename(
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.bmp *.webp *.gif")
            ]
        )
        if f_path:
            self.original_image = Image.open(f_path).convert("RGB")
            self.base_image = self.original_image.copy()
            self.preview_image = self.base_image.copy()

            self.eraser_mask = np.zeros(
                (self.base_image.height, self.base_image.width), dtype=np.uint8
            )
            self.drawing_layer = Image.new(
                "RGBA", self.base_image.size, (0, 0, 0, 0)
            )

            self.reset_sliders_ui()
            self.active_filter = None

            self.w_entry.delete(0, tk.END)
            self.w_entry.insert(0, str(self.base_image.width))
            self.h_entry.delete(0, tk.END)
            self.h_entry.insert(0, str(self.base_image.height))

            self.populate_filter_gallery()
            self.display_image(self.base_image)

    def save_image(self):
        img_to_save = self.preview_image or self.base_image
        if img_to_save is None:
            messagebox.showwarning("Warning", "No image loaded to save!")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg"),
                ("BMP Image", "*.bmp"),
                ("WEBP Image", "*.webp"),
            ],
        )

        if save_path:
            ext = os.path.splitext(save_path)[1].lower()
            save_img = img_to_save.copy()

            if ext in [".jpg", ".jpeg"] and save_img.mode in ("RGBA", "P"):
                save_img = save_img.convert("RGB")

            save_img.save(save_path)
            messagebox.showinfo(
                "Saved", f"File saved successfully as {ext.upper()}!"
            )

    def reset_to_original(self):
        if self.original_image:
            self.base_image = self.original_image.copy()
            self.eraser_mask = np.zeros(
                (self.base_image.height, self.base_image.width), dtype=np.uint8
            )
            self.clear_drawing_layer()
            self.discard_adjustments()
            self.populate_filter_gallery()

    def flip_image(self, direction):
        if self.base_image:
            method = (
                Image.FLIP_LEFT_RIGHT
                if direction == "H"
                else Image.FLIP_TOP_BOTTOM
            )
            self.base_image = self.base_image.transpose(method)
            self.eraser_mask = np.zeros(
                (self.base_image.height, self.base_image.width), dtype=np.uint8
            )
            self.clear_drawing_layer()
            self.update_live_preview()
            self.populate_filter_gallery()

    def apply_resize(self):
        if self.base_image:
            try:
                w, h = int(self.w_entry.get()), int(self.h_entry.get())
                self.base_image = self.base_image.resize(
                    (w, h), Image.Resampling.LANCZOS
                )
                self.eraser_mask = np.zeros(
                    (self.base_image.height, self.base_image.width),
                    dtype=np.uint8,
                )
                self.clear_drawing_layer()
                self.update_live_preview()
                self.populate_filter_gallery()
            except ValueError:
                messagebox.showerror(
                    "Error", "Please enter valid integer dimensions."
                )

    def on_tab_change(self, event):
        if "Filters" in self.get_active_tab_title():
            self.populate_filter_gallery()

    def toggle_crop_mode(self):
        self.crop_mode = not self.crop_mode
        self.crop_btn.config(
            text="Cancel Crop Tool" if self.crop_mode else "Enable Crop Tool"
        )
        if not self.crop_mode and self.crop_rect:
            self.canvas.delete(self.crop_rect)

    def on_crop_press(self, event):
        if self.preview_image is None:
            return
        self.crop_start_x, self.crop_start_y = event.x, event.y
        if self.crop_rect:
            self.canvas.delete(self.crop_rect)
        self.crop_rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="red", width=2, dash=(4, 4)
        )

    def on_crop_drag(self, event):
        if self.crop_rect:
            self.canvas.coords(
                self.crop_rect,
                self.crop_start_x,
                self.crop_start_y,
                event.x,
                event.y,
            )

    def on_crop_release(self, event):
        if self.preview_image is None:
            return

        scale_x = self.preview_image.width / self.preview_w
        scale_y = self.preview_image.height / self.preview_h

        x1 = int((min(self.crop_start_x, event.x) - self.offset_x) * scale_x)
        y1 = int((min(self.crop_start_y, event.y) - self.offset_y) * scale_y)
        x2 = int((max(self.crop_start_x, event.x) - self.offset_x) * scale_x)
        y2 = int((max(self.crop_start_y, event.y) - self.offset_y) * scale_y)

        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(self.preview_image.width, x2), min(
            self.preview_image.height, y2
        )

        if x2 - x1 > 10 and y2 - y1 > 10:
            self.base_image = self.preview_image.crop((x1, y1, x2, y2))
            self.eraser_mask = np.zeros(
                (self.base_image.height, self.base_image.width), dtype=np.uint8
            )
            self.clear_drawing_layer()
            self.toggle_crop_mode()
            self.discard_adjustments()
            self.populate_filter_gallery()


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()