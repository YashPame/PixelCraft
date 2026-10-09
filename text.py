from tkinter import *
from tkinter import font

FONTS = ["Segoe UI Black", "Segoe UI Semibold", "Century Gothic", "Franklin Gothic Demi",
         "Gill Sans MT", "Trebuchet MS", "Candara", "Corbel", "Tw Cen MT",
         "Rockwell", "Georgia", "Constantia", "Palatino Linotype", "Segoe Script",
         "Segoe Print", "Ink Free", "Lucida Handwriting", "Impact"]

root = Tk()
root.title("Pick a heading font")
root.config(bg="white")
installed = font.families()

frame = Frame(root, bg="white")
frame.pack(padx=20, pady=20)
for i, name in enumerate(f for f in FONTS if f in installed):
    row, col = divmod(i, 3)
    cell = Frame(frame, bg="white")
    cell.grid(row=row, column=col, padx=25, pady=10, sticky="w")
    Label(cell, text="PixelCraft", font=(name, 22, "bold"), fg="#2f3775", bg="white").pack(anchor="w")
    Label(cell, text=name, font=("Segoe UI", 9), fg="#7c829a", bg="white").pack(anchor="w")

root.mainloop()