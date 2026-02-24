import ee
import numpy as np
import matplotlib.pyplot as plt
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
    
    days_in_month = datetime(year, month, 1).replace(day=28).day + 3
    days_in_month = min(days_in_month, 28) if month == 2 else min(days_in_month, {1:31,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}[month])
    
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
        
        region = polygon.bounds().getInfo()['coordinates']
        url = image.getThumbURL({
            'region': region,
            'dimensions': 1920,
            'format': 'png',
            'min': TEMP_MIN,
            'max': TEMP_MAX,
            'palette': VIS_PALETTE,
        })
        
        import requests
        from io import BytesIO
        from PIL import Image
        
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img_np = np.array(img)
        
        plt.figure(figsize=(12, 8))
        plt.imshow(img_np)
        plt.axis('off')
        
        date_str = f"{year}-{month:02d}"
        plt.text(
            img_np.shape[1] - 30,
            img_np.shape[0] - 30,
            date_str,
            color='white',
            fontsize=30,
            fontweight='bold',
            ha='right',
            va='bottom',
            bbox=dict(facecolor='black', alpha=0.5, pad=5)
        )
        
        output_dir = os.path.join(DEFAULT_OUTPUT_DIR, place_name)
        os.makedirs(output_dir, exist_ok=True)
        
        save_path = os.path.join(output_dir, f"{place_name}_weather_{year}_{month:02d}.png")
        plt.savefig(save_path, bbox_inches='tight', pad_inches=0.1, dpi=200)
        plt.close()
        
        print(f"Saved: {save_path}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    try:
        place_name, year, month, lat_top, lat_bottom, lon_left, lon_right = get_weather_inputs()
        get_weather_image(place_name, year, month, lat_top, lat_bottom, lon_left, lon_right)
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")
