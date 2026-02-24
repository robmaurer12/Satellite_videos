import ee
import numpy as np
import matplotlib.pyplot as plt
import os
import time
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_satellite_image_inputs, DEFAULT_OUTPUT_DIR

ee.Initialize(project='solid-bliss-390413')


def get_landsat_config(year: int) -> dict:
    if year > 2012:
        landsat = 8
    elif 1984 <= year <= 2010:
        landsat = 5
    elif 2011 <= year <= 2012:
        landsat = 7
    else:
        landsat = 8
    
    if landsat == 8:
        return {
            "collection_id": "LANDSAT/LC08/C02/T1",
            "vmin": 7000,
            "vmax": 21000,
            "band_red": "B4",
            "band_green": "B3",
            "band_blue": "B2"
        }
    elif landsat == 5:
        return {
            "collection_id": "LANDSAT/LT05/C02/T1_L2",
            "vmin": 7000,
            "vmax": 21000,
            "band_red": "SR_B3",
            "band_green": "SR_B2",
            "band_blue": "SR_B1"
        }
    elif landsat == 7:
        return {
            "collection_id": "LANDSAT/LE07/C02/T1_TOA",
            "vmin": 0.07,
            "vmax": 0.30,
            "band_red": "B3",
            "band_green": "B2",
            "band_blue": "B1"
        }
    raise ValueError(f"Unsupported year: {year}")


def download_satellite_images(
    place_name: str,
    start_year: int,
    stop_year: int,
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
    
    output_dir = os.path.join(DEFAULT_OUTPUT_DIR, place_name)
    os.makedirs(output_dir, exist_ok=True)
    
    for year in range(start_year, stop_year + 1):
        try:
            start_time = time.time()
            config = get_landsat_config(year)
            
            collection = (
                ee.ImageCollection(config["collection_id"])
                .filterDate(f"{year}-01-01", f"{year}-12-31")
                .filterBounds(polygon)
                .filter(ee.Filter.lt("CLOUD_COVER", 10))
            )
            
            collection_size = collection.size().getInfo()
            if collection_size == 0:
                print(f"[{year}] No images found, skipping.")
                continue
            
            image = collection.median().select([config["band_red"], config["band_green"], config["band_blue"]])
            
            region = polygon.bounds().getInfo()['coordinates']
            url = image.getThumbURL({
                'region': region,
                'dimensions': 2500,
                'bands': [config["band_red"], config["band_green"], config["band_blue"]],
                'format': 'png',
                'min': config["vmin"],
                'max': config["vmax"],
            })
            
            import requests
            from io import BytesIO
            from PIL import Image
            
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
            
            save_path = os.path.join(output_dir, f"{place_name}_{year}.png")
            plt.savefig(save_path, bbox_inches='tight', pad_inches=0, dpi=200)
            plt.close()
            
            end_time = time.time()
            print(f"[{year}] Saved: {save_path}, Runtime: {end_time - start_time:.2f} sec")
            
        except Exception as e:
            print(f"[{year}] Error: {e}")
            continue


if __name__ == "__main__":
    try:
        place_name, start_year, stop_year, lat_top, lat_bottom, lon_left, lon_right = get_satellite_image_inputs()
        download_satellite_images(place_name, start_year, stop_year, lat_top, lat_bottom, lon_left, lon_right)
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")
