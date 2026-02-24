import cv2
import re
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from matplotlib import font_manager
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_video_inputs, DEFAULT_OUTPUT_DIR


FPS = 30
TITLE_SEC = 5
END_PAUSE_SEC = 6.75
HOLD_SEC = 2
FAST_IMG_SEC = 0.35
SLOW_IMG_SEC = 1.0
OUT_W, OUT_H = 1920, 1080


def frames(sec: float) -> int:
    return int(round(FPS * sec))


def numeric_key(path: Path) -> int:
    m = re.search(r"\d+", path.stem)
    return int(m.group()) if m else 0


def make_title_frame(bg_img: np.ndarray, title: str, start_year: int, stop_year: int) -> np.ndarray:
    lines = [title, "Time Lapse", f"{start_year} – {stop_year}"]
    font_path = font_manager.findfont("DejaVu Sans")
    
    pil = Image.fromarray(cv2.cvtColor(bg_img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    pil_font = ImageFont.truetype(font_path, 120)
    line_spacing = 35
    
    text_heights = [draw.textbbox((0, 0), line, font=pil_font)[3] for line in lines]
    total_h = sum(text_heights) + line_spacing * (len(lines) - 1)
    y = (OUT_H - total_h) // 2
    
    for txt, t_h in zip(lines, text_heights):
        bbox = draw.textbbox((0, 0), txt, font=pil_font)
        x = (OUT_W - bbox[2]) // 2
        draw.text((x, y), txt, font=pil_font, fill=(255, 255, 255))
        y += t_h + line_spacing
    
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def make_thanks_frame(last_frame: np.ndarray) -> np.ndarray:
    font_path = font_manager.findfont("DejaVu Sans")
    thanks_text = "Thanks for watching"
    thanks_font = ImageFont.truetype(font_path, 125)
    
    thanks_pil = Image.fromarray(cv2.cvtColor(last_frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(thanks_pil)
    bbox = draw.textbbox((0, 0), thanks_text, font=thanks_font)
    x_thanks = (OUT_W - bbox[2]) // 2
    y_thanks = OUT_H - 500
    draw.text((x_thanks, y_thanks - bbox[3]), thanks_text, font=thanks_font, fill=(255, 255, 255))
    return cv2.cvtColor(np.array(thanks_pil), cv2.COLOR_RGB2BGR)


def create_video(place_name: str, title: str, start_year: int, stop_year: int) -> None:
    folder = Path(DEFAULT_OUTPUT_DIR, place_name)
    outfile = folder / f"{place_name}_TimeLapse.mp4"
    exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif"}
    
    try:
        files = sorted([p for p in folder.iterdir() if p.suffix.lower() in exts], key=numeric_key)
        if not files:
            raise FileNotFoundError("No images found in the folder.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    
    first_raw = cv2.imread(str(files[0]))
    if first_raw is None:
        print("Error: Could not read first image.")
        return
    
    first = cv2.resize(first_raw, (OUT_W, OUT_H), cv2.INTER_AREA)
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(outfile), fourcc, FPS, (OUT_W, OUT_H))
    
    title_frame = make_title_frame(first.copy(), title, start_year, stop_year)
    for _ in range(frames(TITLE_SEC)):
        writer.write(title_frame)
    
    label_pos = (20, OUT_H - 40)
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2
    thick = 3
    fast_repeat = frames(FAST_IMG_SEC)
    slow_repeat = frames(SLOW_IMG_SEC)
    frames_hold = frames(HOLD_SEC)
    
    last_plain_fast = None
    for idx, img_path in enumerate(files):
        frame_plain = cv2.imread(str(img_path))
        if frame_plain is None:
            continue
        if frame_plain.shape[:2] != (OUT_H, OUT_W):
            frame_plain = cv2.resize(frame_plain, (OUT_W, OUT_H), cv2.INTER_AREA)
        
        frame_fast = frame_plain.copy()
        cv2.putText(frame_fast, "fast", label_pos, font_face, font_scale, (255, 255, 255), thick, cv2.LINE_AA)
        
        repeat = frames_hold if idx == 0 else fast_repeat
        for _ in range(repeat):
            writer.write(frame_fast)
        
        last_plain_fast = frame_plain.copy()
    
    first_plain_slow = cv2.imread(str(files[0]))
    if first_plain_slow is None:
        writer.release()
        print("Error: Could not read first slow frame.")
        return
    if first_plain_slow.shape[:2] != (OUT_H, OUT_W):
        first_plain_slow = cv2.resize(first_plain_slow, (OUT_W, OUT_H), cv2.INTER_AREA)
    
    for _ in range(frames_hold):
        writer.write(last_plain_fast)
    for _ in range(frames_hold):
        writer.write(first_plain_slow)
    for _ in range(frames_hold):
        writer.write(last_plain_fast)
    for _ in range(frames_hold):
        writer.write(first_plain_slow)
    
    last_frame = None
    for img_path in files:
        frame_plain = cv2.imread(str(img_path))
        if frame_plain is None:
            continue
        if frame_plain.shape[:2] != (OUT_H, OUT_W):
            frame_plain = cv2.resize(frame_plain, (OUT_W, OUT_H), cv2.INTER_AREA)
        
        frame_slow = frame_plain.copy()
        cv2.putText(frame_slow, "slow", label_pos, font_face, font_scale, (255, 255, 255), thick, cv2.LINE_AA)
        
        for _ in range(slow_repeat):
            writer.write(frame_slow)
        last_frame = frame_slow.copy()
    
    if last_frame is None:
        writer.release()
        print("Error: No valid frames processed.")
        return
    
    for _ in range(frames_hold):
        writer.write(last_frame)
    
    thanks_frame = make_thanks_frame(last_frame)
    for _ in range(frames(END_PAUSE_SEC)):
        writer.write(thanks_frame)
    
    writer.release()
    print(f"Done! Slideshow saved: {outfile}")


if __name__ == "__main__":
    try:
        place_name, title, start_year, stop_year = get_video_inputs()
        create_video(place_name, title, start_year, stop_year)
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")
