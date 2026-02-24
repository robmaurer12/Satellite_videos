import ee
import cv2
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

FPS = 10
OUT_W, OUT_H = 1920, 1080


def get_days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (datetime(year, month + 1, 1) - datetime(year, month, 1)).days


def draw_borders_on_image(img_np, lat_top, lat_bottom, lon_left, lon_right):
    h, w = img_np.shape[:2]
    
    countries = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
    states = ee.FeatureCollection('TIGER/2018/States')
    
    try:
        country_fc = countries.filterBounds(ee.Geometry.Rectangle([lon_left, lat_bottom, lon_right, lat_top]))
        country_geom = country_fc.geometry().coordinates().getInfo()
        
        for feature in country_geom:
            if isinstance(feature[0][0], list):
                for poly in feature:
                    points = np.array([[
                        int((lon - lon_left) / (lon_right - lon_left) * w),
                        int((lat_top - lat) / (lat_top - lat_bottom) * h)
                    ] for lon, lat in poly], np.int32)
                    cv2.polylines(img_np, [points], True, (0, 0, 0), 2)
            else:
                points = np.array([[
                    int((lon - lon_left) / (lon_right - lon_left) * w),
                    int((lat_top - lat) / (lat_top - lat_bottom) * h)
                ] for lon, lat in feature], np.int32)
                cv2.polylines(img_np, [points], True, (0, 0, 0), 2)
    except:
        pass
    
    try:
        state_fc = states.filterBounds(ee.Geometry.Rectangle([lon_left, lat_bottom, lon_right, lat_top]))
        state_geom = state_fc.geometry().coordinates().getInfo()
        
        for feature in state_geom:
            if isinstance(feature[0][0], list):
                for poly in feature:
                    points = np.array([[
                        int((lon - lon_left) / (lon_right - lon_left) * w),
                        int((lat_top - lat) / (lat_top - lat_bottom) * h)
                    ] for lon, lat in poly], np.int32)
                    cv2.polylines(img_np, [points], True, (50, 50, 50), 1)
            else:
                points = np.array([[
                    int((lon - lon_left) / (lon_right - lon_left) * w),
                    int((lat_top - lat) / (lat_top - lat_bottom) * h)
                ] for lon, lat in feature], np.int32)
                cv2.polylines(img_np, [points], True, (50, 50, 50), 1)
    except:
        pass
    
    return img_np


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
                temp_visualized = img.visualize(
                    min=TEMP_MIN, max=TEMP_MAX, palette=','.join(VIS_PALETTE)
                )
                
                url = temp_visualized.getThumbURL({
                    'region': region,
                    'dimensions': 1920,
                    'format': 'png',
                })
                
                response = requests.get(url)
                pil_img = Image.open(BytesIO(response.content))
                pil_img = pil_img.resize((OUT_W, OUT_H), Image.LANCZOS)
                
                img_np = np.array(pil_img)
                
                img_np = draw_borders_on_image(img_np, lat_top, lat_bottom, lon_left, lon_right)
                
                h, w = img_np.shape[:2]
                
                day_num = (i * days_in_month) // num_images + 1
                day_num = min(day_num, days_in_month)
                date_str = f"{day_num:02d}-{month:02d}-{year}"
                
                fig = plt.figure(figsize=(w/100, h/100), dpi=100)
                fig.patch.set_facecolor('black')
                ax = fig.add_axes([0, 0, 1, 1])
                ax.imshow(img_np)
                ax.set_axis_off()
                
                ax.text(
                    w - 30,
                    h - 30,
                    date_str,
                    color='white',
                    fontsize=28,
                    fontweight='bold',
                    ha='right',
                    va='bottom',
                    bbox=dict(facecolor='black', alpha=0.7, pad=5, edgecolor='white')
                )
                
                legend_w = int(w * 0.25)
                legend_h = 20
                legend_y = h - 60
                
                legend_img = np.zeros((legend_h, legend_w, 3), dtype=np.uint8)
                temps = np.linspace(TEMP_MIN, TEMP_MAX, legend_w)
                for x in range(legend_w):
                    t = temps[x]
                    t_norm = (t - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)
                    idx = int(t_norm * (len(VIS_PALETTE) - 1))
                    color = VIS_PALETTE[idx]
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    legend_img[:, x] = [b, g, r]
                
                ax.imshow(legend_img, extent=[20, legend_w + 20, legend_y, legend_y + legend_h], aspect='auto')
                
                temps_c = np.linspace(TEMP_MIN - 273.15, TEMP_MAX - 273.15, 5)
                tick_x = np.linspace(20, legend_w + 20, 5)
                for x, t in zip(tick_x, temps_c):
                    ax.text(x, legend_y - 8, f"{int(t)}°C", color='black', fontsize=10, fontweight='bold', ha='center')
                
                frame_path = os.path.join(output_dir, f"weather_frame_{i:04d}.png")
                plt.savefig(frame_path, bbox_inches='tight', pad_inches=0, dpi=100, facecolor='black')
                plt.close()
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
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        place_name, year, month, lat_top, lat_bottom, lon_left, lon_right = get_weather_inputs()
        create_weather_timelapse(place_name, year, month, lat_top, lat_bottom, lon_left, lon_right)
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")
