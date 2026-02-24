import tkinter as tk
from tkinter import messagebox
from typing import Callable

DEFAULT_OUTPUT_DIR = r"C:\Users\Public\Documents"

def get_text_input(title: str, labels: list[str], defaults: list[str]) -> list[str]:
    root = tk.Tk()
    root.title(title)
    root.resizable(False, False)

    entries = []
    for i, (txt, default) in enumerate(zip(labels, defaults)):
        tk.Label(root, text=txt).grid(row=i, column=0, sticky="e", padx=8, pady=4)
        e = tk.Entry(root, width=30)
        e.insert(0, str(default))
        e.grid(row=i, column=1, padx=8, pady=4)
        entries.append(e)

    def submit():
        root.quit()

    tk.Button(root, text="OK", width=10, command=submit).grid(
        row=len(labels), columnspan=2, pady=10
    )
    root.mainloop()

    vals = [e.get().strip() for e in entries]
    root.destroy()
    return vals


def get_video_inputs() -> tuple[str, str, int, int]:
    defaults = ["Cabo", "Cabo, Mexico", 1992, 2025]
    labels = ["Place name:", "Title:", "Start year:", "Stop year:"]
    vals = get_text_input("Timelapse parameters", labels, defaults)
    return vals[0], vals[1], int(vals[2]), int(vals[3])


def get_thumbnail_inputs() -> tuple[str, str, int]:
    defaults = ["mecca", "Cabo, Mexico\nTimelapse", 2025]
    labels = ["Folder:", "Caption:", "Year:"]
    
    root = tk.Tk()
    root.title("Thumbnail parameters")
    root.resizable(False, False)

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

    def submit():
        root.quit()

    tk.Button(root, text="OK", width=10, command=submit).grid(row=len(labels), columnspan=2, pady=10)
    root.mainloop()

    vals = []
    for e in entries:
        if isinstance(e, tk.Text):
            vals.append(e.get("1.0", "end-1c").strip())
        else:
            vals.append(e.get().strip())
    root.destroy()
    return vals[0], vals[1], int(vals[2])


def get_satellite_image_inputs() -> tuple[str, int, int, float, float, float, float]:
    root = tk.Tk()
    root.title("Landsat composite parameters")

    tk.Label(root, text="Place name:").grid(row=0, column=0, sticky="e")
    place_var = tk.StringVar(value="test")
    tk.Entry(root, textvariable=place_var, width=25).grid(row=0, column=1)

    tk.Label(root, text="Start year:").grid(row=1, column=0, sticky="e")
    start_var = tk.IntVar(value=2024)
    tk.Spinbox(root, from_=1980, to=2030, textvariable=start_var, width=15).grid(row=1, column=1)

    tk.Label(root, text="Stop year:").grid(row=2, column=0, sticky="e")
    stop_var = tk.IntVar(value=2024)
    tk.Spinbox(root, from_=1980, to=2030, textvariable=stop_var, width=15).grid(row=2, column=1)

    tk.Label(root, text="Lat top:").grid(row=3, column=0, sticky="e")
    lat_top_var = tk.DoubleVar(value=22.8474)
    tk.Entry(root, textvariable=lat_top_var, width=15).grid(row=3, column=1)

    tk.Label(root, text="Lat bottom:").grid(row=4, column=0, sticky="e")
    lat_bottom_var = tk.DoubleVar(value=23.1716)
    tk.Entry(root, textvariable=lat_bottom_var, width=15).grid(row=4, column=1)

    tk.Label(root, text="Lon left:").grid(row=5, column=0, sticky="e")
    lon_left_var = tk.DoubleVar(value=-110.1356)
    tk.Entry(root, textvariable=lon_left_var, width=15).grid(row=5, column=1)

    tk.Label(root, text="Lon right:").grid(row=6, column=0, sticky="e")
    lon_right_var = tk.DoubleVar(value=-109.5602)
    tk.Entry(root, textvariable=lon_right_var, width=15).grid(row=6, column=1)

    tk.Label(root, text="Lon / Lat ratio:").grid(row=7, column=0, sticky="e")
    ratio_var = tk.StringVar(value="")
    ratio_entry = tk.Entry(root, textvariable=ratio_var, width=15, state="readonly")
    ratio_entry.grid(row=7, column=1)

    def update_ratio(*_):
        try:
            lat_diff = abs(lat_bottom_var.get() - lat_top_var.get())
            lon_diff = abs(lon_right_var.get() - lon_left_var.get())
            ratio = lon_diff / lat_diff if lat_diff else float("inf")
            ratio_var.set(f"{ratio:.4f}")
        except tk.TclError:
            ratio_var.set("Err")

    for var in (lat_top_var, lat_bottom_var, lon_left_var, lon_right_var):
        var.trace_add("write", update_ratio)
    update_ratio()

    def launch_map():
        open_map()
        messagebox.showinfo("Instructions", "Click the map to see lat/lon.\nCopy them into the input boxes manually.")

    tk.Button(root, text="Open Map", command=launch_map).grid(row=8, column=0, columnspan=2, pady=6)
    tk.Button(root, text="OK", command=root.quit).grid(row=9, column=0, columnspan=2, pady=6)

    root.mainloop()

    result = (
        place_var.get().strip() or "Unknown",
        int(start_var.get()),
        int(stop_var.get()),
        float(lat_top_var.get()),
        float(lat_bottom_var.get()),
        float(lon_left_var.get()),
        float(lon_right_var.get())
    )
    root.destroy()
    return result


def open_map():
    import threading
    from http.server import SimpleHTTPRequestHandler
    import socketserver
    import webbrowser
    import folium

    PORT = 8000

    def serve_map():
        handler = SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            print(f"Serving map on http://localhost:{PORT}")
            httpd.serve_forever()

    m = folium.Map(location=[22.8474, -109.5602], zoom_start=8)
    folium.LatLngPopup().add_to(m)
    map_file = "map.html"
    m.save(map_file)
    
    threading.Thread(target=serve_map, daemon=True).start()
    webbrowser.open(f"http://localhost:{PORT}/{map_file}")
