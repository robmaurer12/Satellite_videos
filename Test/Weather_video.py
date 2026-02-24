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

FPS = 10
OUT_W, OUT_H = 1920, 1080


def get_days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (datetime(year, month + 1, 1) - datetime(year, month, 1)).days


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0))


def create_weather_timelapse(
    place_name: str,
    year: int,
    month: int,
    lat_top: float,
    lat_bottom: float,
    lon_left: float,
    lon_right: float
) -> None:
    print("Starting weather timelapse generation...")
    
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
    
    print(f"Fetching weather data for {start_date} to {end_date}...")
    
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
    
    print(f"Found {num_images} images, processing frames...")
    
    import requests
    from PIL import Image
    from io import BytesIO
    
    region = polygon.bounds().getInfo()['coordinates']
    frame_files = []
    
    states = ee.FeatureCollection('projects/ee-robertmaurer28/assets/states2')
    
    for i in range(num_images):
        try:
            img = ee.Image(collection_list.get(i))
            
            vis_image = img.visualize(
                min=TEMP_MIN, max=TEMP_MAX, palette=','.join(VIS_PALETTE)
            )
            
            url = vis_image.getThumbURL({
                'region': region,
                'dimensions': [OUT_W, OUT_H],
                'format': 'png',
            })
            
            response = requests.get(url)
            pil_img = Image.open(BytesIO(response.content))
            pil_img = pil_img.convert('RGB')
            pil_img = pil_img.resize((OUT_W, OUT_H), Image.LANCZOS)
            
            img_np = np.array(pil_img)
            
            h, w = img_np.shape[:2]
            
            try:
                state_fc = states.filterBounds(polygon)
                state_list = state_fc.toList(100).getInfo()
                
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
            
            day_num = (i * days_in_month) // num_images + 1
            day_num = min(day_num, days_in_month)
            date_str = f"{day_num:02d}-{month:02d}-{year}"
            cv2.putText(img_np, date_str, (w - 200, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3, cv2.LINE_AA)
            
            legend_w = 400
            legend_h = 30
            legend_x = 50
            legend_y = h - 100
            
            for j in range(legend_w):
                t = j / legend_w
                temp_k = TEMP_MIN + t * (TEMP_MAX - TEMP_MIN)
                idx = int(t * (len(VIS_PALETTE) - 1))
                color = hex_to_rgb(VIS_PALETTE[idx])
                cv2.line(img_np, (legend_x + j, legend_y), (legend_x + j, legend_y + legend_h), color, 1)
            
            temps_c = [int(TEMP_MIN - 273.15), int(TEMP_MAX - 273.15)]
            cv2.putText(img_np, f"{temps_c[0]}C", (legend_x, legend_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(img_np, f"{temps_c[1]}C", (legend_x + legend_w - 50, legend_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
            
            frame_path = os.path.join(output_dir, f"weather_frame_{i:04d}.png")
            cv2.imwrite(frame_path, img_np)
            frame_files.append(frame_path)
            
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{num_images} frames")
                
        except Exception as e:
            print(f"Error processing frame {i}: {e}")
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


if __name__ == "__main__":
    try:
        place_name, year, month, lat_top, lat_bottom, lon_left, lon_right = get_weather_inputs()
        create_weather_timelapse(place_name, year, month, lat_top, lat_bottom, lon_left, lon_right)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
