import cv2, re
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from matplotlib import font_manager
import tkinter as tk

def get_user_inputs():
    root = tk.Tk()
    root.title("Timelapse parameters")
    root.resizable(False, False)
    labels = ["Folder:", "Caption:", "Year:"]
    defaults = ["mecca", "Cabo, Mexico\nTimelapse", 2025]
    entries = []
    for i, (txt, default) in enumerate(zip(labels, defaults)):
        tk.Label(root, text=txt).grid(row=i, column=0, sticky="e", padx=8, pady=4)
        if txt == "Caption:":
            e = tk.Text(root, width=30, height=3)
            e.insert("1.0", str(default))
        else:
            e = tk.Entry(root, width=30)
            e.insert(0, str(default))
        e.grid(row=i, column=1, padx=8, pady=4)
        entries.append(e)
    def _submit():
        root.quit()
    tk.Button(root, text="OK", width=10, command=_submit).grid(row=len(labels), columnspan=2, pady=10)
    root.mainloop()
    vals = []
    for e in entries:
        if isinstance(e, tk.Text):
            vals.append(e.get("1.0", "end-1c").strip())
        else:
            vals.append(e.get().strip())
    root.destroy()
    return vals[0], vals[1], int(vals[2])

Folder, Caption, year = get_user_inputs()
folder = Path(r"C:\Users\Public\Documents", Folder)
base_file = folder / f"{Folder}_{year}.png"
out_file = folder / f"{Folder}_thumbnail.png"
image = Image.open(base_file).convert("RGBA")
try:
    font_path = font_manager.findfont(font_manager.FontProperties(family="Arial"))
    font = ImageFont.truetype(font_path, size=int(image.height / 5))
except:
    font = ImageFont.load_default()
draw = ImageDraw.Draw(image)
lines = Caption.split("\n")
line_spacing = int(font.size * 1.2)
line_sizes = [draw.textbbox((0, 0), line, font=font) for line in lines]
line_widths = [bbox[2] - bbox[0] for bbox in line_sizes]
line_heights = [bbox[3] - bbox[1] for bbox in line_sizes]
text_block_width = max(line_widths)
text_block_height = sum(line_heights) + line_spacing * (len(lines) - 1)
x_text = (image.width - text_block_width) // 2
y_text = (image.height - text_block_height) // 2
draw = ImageDraw.Draw(image)
current_y = y_text
for i, line in enumerate(lines):
    line_width = line_widths[i]
    x_line = (image.width - line_width) // 2
    
    # Outer stroke (black)
    draw.text(
        (x_line, current_y),
        line,
        font=font,
        fill=(255, 255, 255, 0),
        stroke_width=10,
        stroke_fill=(0, 0, 0, 255)
    )

    # Outer stroke (orange)
    draw.text(
        (x_line, current_y),
        line,
        font=font,
        fill=(255, 255, 255, 0),
        stroke_width=4,
        stroke_fill=(255, 55, 0, 255)
    )
    
    # Inner stroke (yellow)
    draw.text(
        (x_line, current_y),
        line,
        font=font,
        fill=(255, 255, 255, 0),
        stroke_width=2,
        stroke_fill=(255, 255, 0, 255)
    )
    
    # Main text (white)
    draw.text(
        (x_line, current_y),
        line,
        font=font,
        fill=(255, 255, 255, 255)
    )

    current_y += line_heights[i] + line_spacing
new_size = (image.width // 2, image.height // 2)
image = image.resize(new_size, Image.LANCZOS)
image.save(out_file)
print(f"Thumbnail saved to {out_file}")
