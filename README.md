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

1. Clone the repository:
```bash
git clone https://github.com/robmaurer12/Satellite_videos.git
cd Satellite_videos
```

2. Install dependencies:
```bash
pip install earthengine-api opencv-python numpy Pillow matplotlib folium requests
```

3. Authenticate with Google Earth Engine:
```bash
earthengine authenticate
```

## Usage

### Option 1: GUI Launcher

Run the main launcher to access all tools through a simple GUI:

```bash
python Test/main.py
```

### Option 2: Command Line

Run individual modules directly from the command prompt:

```bash
# Download satellite images
python Test/Satellite_image.py

# Create time-lapse video
python Test/Satellite_video.py

# Create thumbnail
python Test/Video_thumbnail.py
```

## Workflow

1. **Download Images** - Run `Satellite_image.py` to download Landsat images for your chosen location and years
2. **Create Video** - Run `Satellite_video.py` to generate a time-lapse MP4 from the downloaded images
3. **Add Thumbnail** (optional) - Run `Video_thumbnail.py` to create a thumbnail for the video

## Configuration

Default output directory: `C:\Users\Public\Documents\{place_name\}`

Set your Google Earth Engine project in `Satellite_image.py`:
```python
ee.Initialize(project='your-project-id')
```

## Code Grade: 80/100

See [CODE_REVIEW.md](./CODE_REVIEW.md) for detailed code review and improvement recommendations.
