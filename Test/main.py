import tkinter as tk
import subprocess
import sys
import os
import sys as _sys

def run_script(script_name: str) -> None:
    if not script_name:
        return
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    subprocess.Popen([sys.executable, script_path])

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Satellite Weather Tools")
    root.geometry("270x440")

    buttons = [
        ("Get Satellite Images", "Satellite_image.py", True),
        ("Create Satellite Video", "Satellite_video.py", True),
        ("Create Thumbnail", "Video_thumbnail.py", True),
        ("Get Weather Image", "Weather_image.py", True),
        ("Create Weather Video", "Weather_video.py", True),
    ]

    for label, script, enabled in buttons:
        btn = tk.Button(
            root,
            text=label,
            width=20,
            height=2,
            command=lambda s=script: run_script(s),
            state="normal" if enabled else "disabled"
        )
        btn.pack(pady=6)

    root.mainloop()
