import ee
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_weather_inputs, DEFAULT_OUTPUT_DIR

ee.Initialize(project='solid-bliss-390413')

VIS_PALETTE = [
    '#000066', '#000099', '#2200B4', '#6600FF', '#9900FF', '#0000FF', 
    '#0E6DC4', '#5BADFF', '#69E1FD', '#66FFFF', '#93FFFF', '#66FF33', 
    '#FFFF00', '#FFCC00', '#FF9933', '#FF6600', '#FF0000', '#CC0000', 
    '#F5496E', '#FFCCFF'
]
TEMP_MIN = 223
TEMP_MAX = 318


def get_weather_image(
    place_name: str,
    year: int,
    month: int,
    lat_top: float,
    lat_bottom: float,
    lon_left: float,
    lon_right: float
) -> None:
    polygon = ee.Geometry.Polygon([
        [[lon_right, lat_top],
         [lon_left, lat_top],
         [lon_left, lat_bottom],
         [lon_right, lat_bottom]]
    ])
    
    days_in_month = (datetime(year, month + 1, 1) - datetime(year, month, 1)).days if month < 12 else 31
    
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{days_in_month:02d}"
    
    try:
        collection = (
            ee.ImageCollection('NOAA/CFSV2/FOR6H')
            .select('Temperature_height_above_ground')
            .filter(ee.Filter.date(start_date, end_date))
        )
        
        collection_size = collection.size().getInfo()
        if collection_size == 0:
            print(f"No weather data found for {year}-{month:02d}")
            return
        
        image = collection.median()
        
        temp_visualized = image.visualize(
            min=TEMP_MIN, max=TEMP_MAX, palette=','.join(VIS_PALETTE)
        )
        
        region = polygon.bounds().getInfo()['coordinates']
        url = temp_visualized.getThumbURL({
            'region': region,
            'dimensions': 1920,
            'format': 'png',
        })
        
        import requests
        from io import BytesIO
        from PIL import Image
        
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img_np = np.array(img)
        
        fig = plt.figure(figsize=(12, 8), facecolor='black')
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(img_np)
        ax.set_axis_off()
        
        date_str = f"{days_in_month:02d}-{month:02d}-{year}"
        ax.text(
            img_np.shape[1] - 30,
            img_np.shape[0] - 30,
            date_str,
            color='white',
            fontsize=24,
            fontweight='bold',
            ha='right',
            va='bottom',
            bbox=dict(facecolor='black', alpha=0.6, pad=5, edgecolor='white')
        )
        
        ax_legend = fig.add_axes([0.01, 0.01, 0.25, 0.02])
        temps_k = np.linspace(TEMP_MIN, TEMP_MAX, 256).reshape(1, -1)
        cmap = mcolors.LinearSegmentedColormap.from_list('temp', VIS_PALETTE)
        ax_legend.imshow(temps_k, cmap=cmap, aspect='auto')
        ax_legend.set_axis_off()
        
        temps_c = np.linspace(TEMP_MIN - 273.15, TEMP_MAX - 273.15, 5)
        tick_positions = np.linspace(0, 255, 5)
        tick_labels = [f"{int(t)}°C" for t in temps_c]
        ax_legend.set_xticks(tick_positions)
        ax_legend.set_xticklabels(tick_labels, color='black', fontsize=8, fontweight='bold')
        
        for tick in ax_legend.xaxis.get_major_ticks():
            tick.label1.set_color('black')
        
        output_dir = os.path.join(DEFAULT_OUTPUT_DIR, place_name)
        os.makedirs(output_dir, exist_ok=True)
        
        save_path = os.path.join(output_dir, f"{place_name}_weather_{year}_{month:02d}.png")
        plt.savefig(save_path, bbox_inches=None, pad_inches=0, dpi=150, facecolor='white')
        plt.close()
        
        print(f"Saved: {save_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        place_name, year, month, lat_top, lat_bottom, lon_left, lon_right = get_weather_inputs()
        get_weather_image(place_name, year, month, lat_top, lat_bottom, lon_left, lon_right)
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")
