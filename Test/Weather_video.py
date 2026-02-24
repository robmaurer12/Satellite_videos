import ee
import cv2
import numpy as np
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

FPS = 10
OUT_W, OUT_H = 1920, 1080


def get_days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (datetime(year, month + 1, 1) - datetime(year, month, 1)).days


def create_weather_timelapse(
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
    
    days_in_month = get_days_in_month(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{days_in_month:02d}"
    
    output_dir = os.path.join(DEFAULT_OUTPUT_DIR, place_name)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        print("Fetching weather data...")
        collection = (
            ee.ImageCollection('NOAA/CFSV2/FOR6H')
            .select('Temperature_height_above_ground')
            .filter(ee.Filter.date(start_date, end_date))
        )
        
        collection_list = collection.toList(collection.size().getInfo())
        num_images = collection_list.length().getInfo()
        
        if num_images == 0:
            print(f"No weather data found for {year}-{month:02d}")
            return
        
        print(f"Found {num_images} images, downloading frames...")
        
        import requests
        from io import BytesIO
        from PIL import Image
        
        region = polygon.bounds().getInfo()['coordinates']
        frame_files = []
        
        for i in range(num_images):
            try:
                img = ee.Image(collection_list.get(i))
                url = img.getThumbURL({
                    'region': region,
                    'dimensions': 1920,
                    'format': 'png',
                    'min': TEMP_MIN,
                    'max': TEMP_MAX,
                    'palette': VIS_PALETTE,
                })
                
                response = requests.get(url)
                pil_img = Image.open(BytesIO(response.content))
                pil_img = pil_img.resize((OUT_W, OUT_H), Image.LANCZOS)
                
                frame_path = os.path.join(output_dir, f"weather_frame_{i:04d}.png")
                pil_img.save(frame_path)
                frame_files.append(frame_path)
                
                if (i + 1) % 10 == 0:
                    print(f"Downloaded {i + 1}/{num_images} frames")
                    
            except Exception as e:
                print(f"Error downloading frame {i}: {e}")
                continue
        
        if len(frame_files) < 2:
            print("Not enough frames to create video")
            return
        
        print("Creating video...")
        out_file = os.path.join(output_dir, f"{place_name}_weather_{year}_{month:02d}.mp4")
        
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(out_file, fourcc, FPS, (OUT_W, OUT_H))
        
        for frame_file in frame_files:
            frame = cv2.imread(frame_file)
            if frame is not None:
                writer.write(frame)
        
        writer.release()
        
        for frame_file in frame_files:
            try:
                os.remove(frame_file)
            except:
                pass
        
        print(f"Done! Video saved: {out_file}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    try:
        place_name, year, month, lat_top, lat_bottom, lon_left, lon_right = get_weather_inputs()
        create_weather_timelapse(place_name, year, month, lat_top, lat_bottom, lon_left, lon_right)
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")
