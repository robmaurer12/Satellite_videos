import ee
import numpy as np
import cv2
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


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0))


def get_weather_image(
    place_name: str,
    year: int,
    month: int,
    lat_top: float,
    lat_bottom: float,
    lon_left: float,
    lon_right: float
) -> None:
    print("Starting weather image generation...")
    
    polygon = ee.Geometry.Polygon([
        [[lon_right, lat_top],
         [lon_left, lat_top],
         [lon_left, lat_bottom],
         [lon_right, lat_bottom]]
    ])
    
    days_in_month = (datetime(year, month + 1, 1) - datetime(year, month, 1)).days if month < 12 else 31
    
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{days_in_month:02d}"
    
    print(f"Fetching data for {start_date} to {end_date}...")
    
    collection = (
        ee.ImageCollection('NOAA/CFSV2/FOR6H')
        .select('Temperature_height_above_ground')
        .filter(ee.Filter.date(start_date, end_date))
    )
    
    collection_size = collection.size().getInfo()
    print(f"Found {collection_size} images")
    
    if collection_size == 0:
        print(f"No weather data found for {year}-{month:02d}")
        return
    
    image = collection.median()
    
    region = polygon.bounds().getInfo()['coordinates']
    
    url = image.getDownloadURL({
        'region': region,
        'dimensions': [1920, 1080],
        'format': 'PNG',
    })
    
    print("Downloading image...")
    import requests
    from PIL import Image
    from io import BytesIO
    
    response = requests.get(url)
    print(f"Response status: {response.status_code}")
    
    img = Image.open(BytesIO(response.content))
    img = img.convert('RGB')
    img = img.resize((1920, 1080))
    img_np = np.array(img)
    
    print("Drawing borders...")
    
    states = ee.FeatureCollection('projects/ee-robertmaurer28/assets/states2')
    
    h, w = img_np.shape[:2]
    
    try:
        state_fc = states.filterBounds(polygon)
        state_list = state_fc.toList(100).getInfo()
        print(f"Found {len(state_list)} states")
        
        for feat in state_list:
            geom = feat['geometry']
            if geom['type'] == 'Polygon':
                coords = geom['coordinates'][0]
                points = np.array([[
                    int((lon - lon_left) / (lon_right - lon_left) * w),
                    int((lat_top - lat) / (lat_top - lat_bottom) * h)
                ] for lon, lat in coords], np.int32)
                cv2.polylines(img_np, [points], True, (80, 80, 80), 2)
            elif geom['type'] == 'MultiPolygon':
                for poly in geom['coordinates']:
                    coords = poly[0]
                    points = np.array([[
                        int((lon - lon_left) / (lon_right - lon_left) * w),
                        int((lat_top - lat) / (lat_top - lat_bottom) * h)
                    ] for lon, lat in coords], np.int32)
                    cv2.polylines(img_np, [points], True, (80, 80, 80), 2)
    except Exception as e:
        print(f"Error drawing states: {e}")
    
    print("Adding date text...")
    date_str = f"{days_in_month:02d}-{month:02d}-{year}"
    cv2.putText(img_np, date_str, (w - 200, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3, cv2.LINE_AA)
    
    print("Adding legend...")
    legend_w = 400
    legend_h = 30
    legend_x = 50
    legend_y = h - 100
    
    for i in range(legend_w):
        t = i / legend_w
        temp_k = TEMP_MIN + t * (TEMP_MAX - TEMP_MIN)
        idx = int(t * (len(VIS_PALETTE) - 1))
        color = hex_to_rgb(VIS_PALETTE[idx])
        cv2.line(img_np, (legend_x + i, legend_y), (legend_x + i, legend_y + legend_h), color, 1)
    
    temps_c = [int(TEMP_MIN - 273.15), int(TEMP_MAX - 273.15)]
    cv2.putText(img_np, f"{temps_c[0]}C", (legend_x, legend_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img_np, f"{temps_c[1]}C", (legend_x + legend_w - 50, legend_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
    
    output_dir = os.path.join(DEFAULT_OUTPUT_DIR, place_name)
    os.makedirs(output_dir, exist_ok=True)
    
    save_path = os.path.join(output_dir, f"{place_name}_weather_{year}_{month:02d}.png")
    cv2.imwrite(save_path, img_np)
    
    print(f"Saved: {save_path}")


if __name__ == "__main__":
    try:
        place_name, year, month, lat_top, lat_bottom, lon_left, lon_right = get_weather_inputs()
        get_weather_image(place_name, year, month, lat_top, lat_bottom, lon_left, lon_right)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
