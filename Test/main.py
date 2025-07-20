import tkinter as tk
import subprocess
import sys
import os

def run_script(script_name: str) -> None:
    """Launch another Python script that lives in this project folder."""
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    subprocess.Popen([sys.executable, script_path])

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Satellite Weather Tools")
    root.geometry("300x220")

    buttons = [
        ("Get Satellite Images", "Satellite_image.py"),
        ("Create Satellite Video", "Satellite_video.py"),
        ("Get Weather", ""),
        ("Create Weather Video", ""),
    ]

    for label, script in buttons:
        tk.Button(
            root,
            text=label,
            width=20,
            height=2,
            command=lambda s=script: run_script(s)
        ).pack(pady=6)

    root.mainloop()
