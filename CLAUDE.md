# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running

Desktop photo editor built with Tkinter. No build system, tests, or linter are configured.

```
python main.py
```

Dependencies (no requirements file): `opencv-python`, `numpy`, `Pillow`. Run from the repo root — icons are loaded relative to the CWD (or `sys._MEIPASS` when frozen with PyInstaller, see `resource_path` in `Components/ui_icons_loader.py`). The app launches fullscreen.

## Architecture

**`main.py` – `PhotoEditorApp`** is the central hub. Every component receives the `App` instance and reaches everything else through it (`App.editor`, `App.action_bar`, `App.status_bar`, `App.canvas_frame`, `App.theme`, ...). Shared Tk variables (`App.hasImage`, `App.activeTopButton`) are attached to `App` by `Components/variables.py`; icons are attached as `App.IconImage_*` by `UIIconsLoader`.

**Layout / scaling:** all positions and sizes are written in a fixed 1536×864 "design pixel" space and scaled to the real screen via `App.ratioW/ratioH`. Always use the helpers rather than raw pixels: `App.place_component(widget, x, y, w, h)`, `App.place_configure`, `App.scale_x/scale_y`, `App.adjust_font(size, bold=)`, and `App.CreateSlider(...)`. Widgets are positioned with `place`, not pack/grid, at the top level. Layout constants (`CANVAS`, `SIDEBAR`, `STATUS`, ...) live in `main.py`.

**Theme:** colors come from the `THEME` dict in `main.py` (exposed as `App.theme`, usually aliased `t`). Don't hardcode colors; defaults are also pushed via `option_add` / ttk `clam` style in `ApplyTheme`.

**UI flow:** `App.hasImage` drives the welcome-screen vs. editor switch — both `App.UpdateButtons` and `ActionBar.UpdateButtons` trace it and rebuild. `ActionBar.TopButtonClicked` destroys/creates a side panel inside a fresh `PanelsFrame` on the right, shifts the canvas left, and tracks the active tool in `App.activeTopButton`. To add a tool: create a panel class in `Components/Panels/`, add a button in `ActionBar.CreateButtons`, and wire it into `GetButtons` and `TopButtonClicked`.

**Panels ↔ Editor contract:** each panel registers itself on `App` (e.g. `self.App.light_panel = self`). `Editor.GetPanel(name)` returns it only if the widget still exists, and the Editor calls back into open panels:
- `SyncSliders()` → `light_panel.SetValues`, `crop_panel.SetAngle`, `filters_panel.Refresh` (after undo/redo/reset/open)
- `ShowImage()` → `crop_panel.DrawCropBox`, `eraser_panel.DrawMask`, `bg_panel.DrawBox` (overlays are redrawn after each image refresh)

Panels that use the left mouse button bind `<ButtonPress-1>` on the canvas; `EditorCanvas` checks for that binding to decide whether left-drag pans (right/middle always pan, via a custom `"Pan"` bindtag).

**Core (`Core/`)** — image processing, no layout code:
- `ImageDocument` holds one open file and its layered state. Images are OpenCV arrays (BGR/BGRA/gray), converted to PIL only for adjustments/filters/display.
  - `base_image` = original after geometric edits (rotate/flip/crop/straighten)
  - `processed_image` = base + `adjustments` dict + `filter_name`
  - `image` = processed + `drawing_layer` (BGRA strokes) composited — what's shown/saved
  - `cutout` (subject with transparent bg, set by background remover), `straighten_source`/`drawing_source` (pre-straighten copies so angles are absolute, not cumulative)
- `Editor` (`Core/image_editor.py`) owns all operations. Edits mutate document fields then call `RenderImage()` (rebuild `processed_image`/`image`, set `modified`) and `ShowImage()` (zoom, center, draw on canvas). Geometric ops go through `Transform(func, ...)` so the drawing layer and cutout stay aligned with the photo. Adjustments are always applied in the fixed `ADJUSTMENT_ORDER`.
- **Undo/redo** snapshots only the fields in `STATE_FIELDS` (zoom is excluded), capped at `MAX_HISTORY`. Call `SaveState()` before a discrete edit; for slider drags use `StartAdjust()`/`EndAdjust()` so one drag = one undo entry (panels debounce slider updates with `after(30, ...)` and pass `save_state=False`). Any new persistent document field that should be undoable must be added to `STATE_FIELDS`.

## Conventions

- Methods use PascalCase (`ShowImage`, `TopButtonClicked`); helpers on `App` are snake_case. Note the existing misspellings `orignal_image` and `IconImage_Brightenss` — they are referenced across files.
- Comments are short, plain-English explanations of *why*; match that style.
