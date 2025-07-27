import ee, numpy as np, matplotlib.pyplot as plt, os, time, tkinter as tk
from io import BytesIO
from PIL import Image
import requests
import folium
import webbrowser
import threading
from http.server import SimpleHTTPRequestHandler
import socketserver

PORT = 8000  # Port for local map server

# Serve map locally
def serve_map():
    handler = SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving map on http://localhost:{PORT}")
        httpd.serve_forever()

# Generate folium map with lat/lon popup
def generate_map_html():
    m = folium.Map(location=[22.8474, -109.5602], zoom_start=8)
    folium.LatLngPopup().add_to(m)
    map_file = "map.html"
    m.save(map_file)
    return map_file

# Open map in browser
def open_map():
    map_file = generate_map_html()
    threading.Thread(target=serve_map, daemon=True).start()
    webbrowser.open(f"http://localhost:{PORT}/{map_file}")

# GUI to get user inputs
def get_user_inputs():
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
    lat_left_var = tk.DoubleVar(value=22.8474)
    tk.Entry(root, textvariable=lat_left_var, width=15).grid(row=3, column=1)

    tk.Label(root, text="Lat bottom:").grid(row=4, column=0, sticky="e")
    lat_right_var = tk.DoubleVar(value=23.1716)
    tk.Entry(root, textvariable=lat_right_var, width=15).grid(row=4, column=1)

    tk.Label(root, text="Lon left:").grid(row=5, column=0, sticky="e")
    lon_top_var = tk.DoubleVar(value=-109.5602)
    tk.Entry(root, textvariable=lon_top_var, width=15).grid(row=5, column=1)

    tk.Label(root, text="Lon right:").grid(row=6, column=0, sticky="e")
    lon_bottom_var = tk.DoubleVar(value=-110.1356)
    tk.Entry(root, textvariable=lon_bottom_var, width=15).grid(row=6, column=1)

    tk.Label(root, text="Lon / Lat ratio:").grid(row=7, column=0, sticky="e")
    ratio_var = tk.StringVar(value="")
    ratio_entry = tk.Entry(root, textvariable=ratio_var, width=15, state="readonly")
    ratio_entry.grid(row=7, column=1)

    def update_ratio(*_):
        try:
            lat_diff = abs(lat_right_var.get() - lat_left_var.get())
            lon_diff = abs(lon_bottom_var.get() - lon_top_var.get())
            ratio = lon_diff / lat_diff if lat_diff else float("inf")
            ratio_var.set(f"{ratio:.4f}")
        except tk.TclError:
            ratio_var.set("Err")

    for var in (lat_left_var, lat_right_var, lon_top_var, lon_bottom_var):
        var.trace_add("write", update_ratio)
    update_ratio()

    def launch_map():
        open_map()
        tk.messagebox.showinfo("Instructions", "Click the map to see lat/lon.\nCopy them into the input boxes manually.")

    tk.Button(root, text="Open Map", command=launch_map).grid(row=8, column=0, columnspan=2, pady=6)
    tk.Button(root, text="OK", command=root.quit).grid(row=9, column=0, columnspan=2, pady=6)

    root.mainloop()

    result = (
        place_var.get().strip() or "Unknown",
        int(start_var.get()),
        int(stop_var.get()),
        float(lat_left_var.get()),
        float(lat_right_var.get()),
        float(lon_top_var.get()),
        float(lon_bottom_var.get())
    )
    root.destroy()
    return result

# --- Get User Input ---
place_name, start_year, stop_year, lat_left, lat_right, lon_top, lon_bottom = get_user_inputs()

# --- Earth Engine Setup ---
ee.Initialize(project='solid-bliss-390413')

polygon = ee.Geometry.Polygon(
    [[[lon_bottom, lat_left], 
      [lon_top, lat_left],
      [lon_top, lat_right], 
      [lon_bottom, lat_right]]]
)

landsat = 8
typee = 2  # 2 = median, else mean

for year in range(start_year, stop_year + 1):
    if year > 2012:
        landsat = 8
    elif 1984 <= year <= 2010:
        landsat = 5
    elif 2011 <= year <= 2012:
        landsat = 7

    if landsat == 8:
        collection_id = "LANDSAT/LC08/C02/T1"
        vmin, vmax = 7000, 21000
        band1, band2, band3 = "B4", "B3", "B2"
    elif landsat == 5:
        collection_id = "LANDSAT/LT05/C02/T1_L2"
        vmin, vmax = 7000, 21000
        band1, band2, band3 = "SR_B3", "SR_B2", "SR_B1"
    elif landsat == 7:
        collection_id = "LANDSAT/LE07/C02/T1_TOA"
        vmin, vmax = 0.07, 0.30
        band1, band2, band3 = "B3", "B2", "B1"

    start_time = time.time()

    collection = (
        ee.ImageCollection(collection_id)
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .filterBounds(polygon)
        .filter(ee.Filter.lt("CLOUD_COVER", 10))
    )

    if collection.size().getInfo() == 0:
        print(f"[{year}] No images found, skipping.")
        continue

    image = collection.median() if typee > 1 else collection.mean()
    image = image.select([band1, band2, band3])

    region = polygon.bounds().getInfo()['coordinates']
    url = image.getThumbURL({
        'region': region,
        'dimensions': 2500,
        'bands': [band1, band2, band3],
        'format': 'png',
        'min': vmin,
        'max': vmax,
    })

    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img_np = np.array(img)

    plt.figure(figsize=(8, 8))
    plt.imshow(img_np)
    plt.axis('off')
    plt.text(
        img_np.shape[1] - 60,
        img_np.shape[0] - 50,
        str(year),
        color='white',
        fontsize=25,
        fontweight='bold',
        ha='right',
        va='bottom',
        bbox=dict(facecolor='black', alpha=0, pad=0)
    )

    output_dir = os.path.join(r"C:\Users\Public\Documents", place_name)
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"{place_name}_{year}.png")

    plt.savefig(save_path, bbox_inches='tight', pad_inches=0, dpi=400)
    end_time = time.time()
    print(f"[{year}] Saved: {save_path}, Runtime: {end_time - start_time:.2f} sec")
