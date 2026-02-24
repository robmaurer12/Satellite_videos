import cv2
import re
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from matplotlib import font_manager
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_thumbnail_inputs, DEFAULT_OUTPUT_DIR


def create_thumbnail(folder_name: str, caption: str, year: int) -> None:
    folder = Path(DEFAULT_OUTPUT_DIR, folder_name)
    base_file = folder / f"{folder_name}_{year}.png"
    out_file = folder / f"{folder_name}_thumbnail.png"
    
    try:
        image = Image.open(base_file).convert("RGBA")
    except FileNotFoundError:
        print(f"Error: File not found: {base_file}")
        return
    except Exception as e:
        print(f"Error opening image: {e}")
        return
    
    try:
        font_path = font_manager.findfont(font_manager.FontProperties(family="Arial"))
        font = ImageFont.truetype(font_path, size=int(image.height / 5))
    except Exception:
        font = ImageFont.load_default()
    
    draw = ImageDraw.Draw(image)
    lines = caption.split("\n")
    line_spacing = int(font.size * 1.2)
    line_sizes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    line_widths = [bbox[2] - bbox[0] for bbox in line_sizes]
    line_heights = [bbox[3] - bbox[1] for bbox in line_sizes]
    text_block_width = max(line_widths)
    text_block_height = sum(line_heights) + line_spacing * (len(lines) - 1)
    x_text = (image.width - text_block_width) // 2
    y_text = (image.height - text_block_height) // 2
    
    current_y = y_text
    for i, line in enumerate(lines):
        line_width = line_widths[i]
        x_line = (image.width - line_width) // 2
        
        draw.text(
            (x_line, current_y),
            line,
            font=font,
            fill=(255, 255, 255, 0),
            stroke_width=10,
            stroke_fill=(0, 0, 0, 255)
        )
        
        draw.text(
            (x_line, current_y),
            line,
            font=font,
            fill=(255, 255, 255, 0),
            stroke_width=4,
            stroke_fill=(255, 55, 0, 255)
        )
        
        draw.text(
            (x_line, current_y),
            line,
            font=font,
            fill=(255, 255, 255, 0),
            stroke_width=2,
            stroke_fill=(255, 255, 0, 255)
        )
        
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


if __name__ == "__main__":
    try:
        folder, caption, year = get_thumbnail_inputs()
        create_thumbnail(folder, caption, year)
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")
