# Satellite Videos

A Python application for creating satellite imagery time-lapse videos from Landsat data.

## Features

- **Get Satellite Images** - Download Landsat satellite imagery for any location and time range
- **Create Satellite Video** - Generate time-lapse videos from satellite images with title cards and transitions
- **Create Thumbnail** - Create stylized thumbnails for videos with custom captions

## Requirements

- Python 3.8+
- Google Earth Engine API key
- Required packages: `earthengine-api`, `opencv-python`, `numpy`, `Pillow`, `matplotlib`, `folium`, `requests`

## Installation

```bash
pip install earthengine-api opencv-python numpy Pillow matplotlib folium requests
```

## Usage

Run `main.py` to access all tools through the GUI:

```bash
python Test/main.py
```

### Individual Modules

- **Satellite_image.py** - Downloads Landsat images for a given location and year range
- **Satellite_video.py** - Creates time-lapse videos from downloaded images
- **Video_thumbnail.py** - Generates thumbnail images with text overlays

## Configuration

Default output directory: `C:\Users\Public\Documents\{place_name\}`

Set your Google Earth Engine project in the code or as an environment variable.

## Code Grade: 55/100

See [CODE_REVIEW.md](./CODE_REVIEW.md) for detailed code review and improvement recommendations.
