import cv2, re
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from matplotlib import font_manager
import tkinter as tk

def get_user_inputs():
    root = tk.Tk()
    root.title("Time‑lapse parameters")
    root.resizable(False, False)

    labels   = ["Place name:", "Title:", "Start year:", "Stop year:"]
    defaults = ["Cabo", "Cabo, Mexico", 1992, 2025]
    entries  = []

    for i, (txt, default) in enumerate(zip(labels, defaults)):
        tk.Label(root, text=txt).grid(row=i, column=0, sticky="e", padx=8, pady=4)
        e = tk.Entry(root, width=30)
        e.insert(0, str(default))
        e.grid(row=i, column=1, padx=8, pady=4)
        entries.append(e)

    def _submit():
        root.quit()                      # end the modal loop

    tk.Button(root, text="OK", width=10, command=_submit).grid(
        row=len(labels), columnspan=2, pady=10
    )
    root.mainloop()

    vals = [e.get().strip() for e in entries]
    root.destroy()
    return vals[0], vals[1], int(vals[2]), int(vals[3])

# grab the values ⟶ they feed the rest of the script
place_name, title, start_year, stop_year = get_user_inputs()

# ─── User‑configurable settings ──────────────────────────────────────────────

folder       = Path(r"C:\Users\Public\Documents", place_name)
outfile      = folder / f"{place_name}_TimeLapse.mp4"
exts         = {".png", ".jpg", ".jpeg", ".bmp", ".tif"}

fps              = 30              # video frame‑rate
title_sec        = 5               # opening title card
end_pause_sec    = 6.75            # final “Thanks” screen length
hold_sec         = 2               # pauses between sections
fast_img_sec     = 0.35            # duration per image in FAST part
slow_img_sec     = 1.0             # duration per image in SLOW part
# Desired output resolution (1080p)
out_w, out_h     = 1920, 1080
# ─────────────────────────────────────────────────────────────────────────────

# Convenience ── how many video frames correspond to a given duration (sec)
def frames(sec):
    return int(round(fps * sec))

# Natural sort helper (extracts first integer in filename)
def numeric_key(path: Path):
    m = re.search(r"\d+", path.stem)
    return int(m.group()) if m else 0

# --------------------------------------------------------------------------- #
#                           Load & prepare source images                      #
# --------------------------------------------------------------------------- #
files = sorted([p for p in folder.iterdir() if p.suffix.lower() in exts], key=numeric_key)
if not files:
    raise FileNotFoundError("No images found in the folder.")

first_raw = cv2.imread(str(files[0]))
if first_raw is None:
    raise FileNotFoundError("Could not read first image.")

w, h = out_w, out_h                                   # force 1080p output
first = cv2.resize(first_raw, (w, h), cv2.INTER_AREA) # resize first frame

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(str(outfile), fourcc, fps, (w, h))

# --------------------------------------------------------------------------- #
#                               Title card                                    #
# --------------------------------------------------------------------------- #
lines = [title, "Time Lapse", f"{start_year} – {stop_year}"]
font_path = font_manager.findfont("DejaVu Sans")

def make_title_frame(bg_img):
    pil = Image.fromarray(cv2.cvtColor(bg_img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    pil_font = ImageFont.truetype(font_path, 120)
    line_spacing = 35

    # Compute vertical centering
    text_heights = [draw.textbbox((0, 0), line, font=pil_font)[3] for line in lines]
    total_h = sum(text_heights) + line_spacing * (len(lines) - 1)
    y = (h - total_h) // 2

    for txt, t_h in zip(lines, text_heights):
        bbox = draw.textbbox((0, 0), txt, font=pil_font)
        x = (w - bbox[2]) // 2
        draw.text((x, y), txt, font=pil_font, fill=(255, 255, 255))
        y += t_h + line_spacing

    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

title_frame = make_title_frame(first.copy())
for _ in range(frames(title_sec)):
    writer.write(title_frame)

# --------------------------------------------------------------------------- #
#                               FAST section                                  #
# --------------------------------------------------------------------------- #
label_pos   = (20, h - 40)
font_face   = cv2.FONT_HERSHEY_SIMPLEX
font_scale  = 2
thick       = 3
fast_repeat = frames(fast_img_sec)        # frames per image in fast section
slow_repeat = frames(slow_img_sec)        # frames per image in slow section
frames_hold = frames(hold_sec)

last_plain_fast = None
for idx, img_path in enumerate(files):
    frame_plain = cv2.imread(str(img_path))
    if frame_plain is None:
        continue
    if frame_plain.shape[:2] != (h, w):
        frame_plain = cv2.resize(frame_plain, (w, h), cv2.INTER_AREA)

    frame_fast = frame_plain.copy()
    cv2.putText(frame_fast, "fast", label_pos, font_face, font_scale, (255, 255, 255), thick, cv2.LINE_AA)

    # Hold the FIRST fast frame a bit longer
    repeat = frames_hold if idx == 0 else fast_repeat
    for _ in range(repeat):
        writer.write(frame_fast)

    last_plain_fast = frame_plain.copy()

# --------------------------------------------------------------------------- #
#                 Pause sequence between FAST and SLOW (no text)              #
# --------------------------------------------------------------------------- #
first_plain_slow = cv2.imread(str(files[0]))
if first_plain_slow is None:
    raise FileNotFoundError("Could not read first slow frame.")
if first_plain_slow.shape[:2] != (h, w):
    first_plain_slow = cv2.resize(first_plain_slow, (w, h), cv2.INTER_AREA)

for _ in range(frames_hold): writer.write(last_plain_fast)
for _ in range(frames_hold): writer.write(first_plain_slow)
for _ in range(frames_hold): writer.write(last_plain_fast)
for _ in range(frames_hold): writer.write(first_plain_slow)

# --------------------------------------------------------------------------- #
#                                SLOW section                                 #
# --------------------------------------------------------------------------- #
last_frame = None
for img_path in files:
    frame_plain = cv2.imread(str(img_path))
    if frame_plain is None:
        continue
    if frame_plain.shape[:2] != (h, w):
        frame_plain = cv2.resize(frame_plain, (w, h), cv2.INTER_AREA)

    frame_slow = frame_plain.copy()
    cv2.putText(frame_slow, "slow", label_pos, font_face, font_scale, (255, 255, 255), thick, cv2.LINE_AA)

    for _ in range(slow_repeat):
        writer.write(frame_slow)
    last_frame = frame_slow.copy()

# --------------------------------------------------------------------------- #
#                        Final hold + “Thanks for watching”                   #
# --------------------------------------------------------------------------- #
for _ in range(frames_hold):
    writer.write(last_frame)

thanks_text  = "Thanks for watching"
thanks_font  = ImageFont.truetype(font_path, 125)

thanks_pil   = Image.fromarray(cv2.cvtColor(last_frame, cv2.COLOR_BGR2RGB))
draw         = ImageDraw.Draw(thanks_pil)
bbox         = draw.textbbox((0, 0), thanks_text, font=thanks_font)
x_thanks     = (w - bbox[2]) // 2
y_thanks     = h - 500
draw.text((x_thanks, y_thanks - bbox[3]), thanks_text, font=thanks_font, fill=(255, 255, 255))
thanks_frame = cv2.cvtColor(np.array(thanks_pil), cv2.COLOR_RGB2BGR)

for _ in range(frames(end_pause_sec)):
    writer.write(thanks_frame)

writer.release()
print("Done! Slideshow saved:", outfile)
