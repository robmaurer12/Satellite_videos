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

## Usage (Windows)

### Option 1: Run with batch file (Recommended)

Simply double-click `run.bat` in the project folder - it will automatically find Python and launch the GUI.

### Option 2: Command Prompt

Run the main launcher:

```cmd
python Test\main.py
```

If Python is not in your PATH, use the full path:

```cmd
C:\Users\YourUsername\AppData\Local\Programs\Python\Python312\python.exe Test\main.py
```

Or find Python in your system and run:

```cmd
where python
```

### Option 3: Command Line

Run individual modules directly:

```cmd
python Test\Satellite_image.py
python Test\Satellite_video.py
python Test\Video_thumbnail.py
```

## Workflow

1. **Download Images** - Run `Satellite_image.py` to download Landsat images for your chosen location and years
2. **Create Video** - Run `Satellite_video.py` to generate a time-lapse MP4 from the downloaded images
3. **Add Thumbnail** (optional) - Run `Video_thumbnail.py` to create a thumbnail for the video

## Configuration

Default output directory: `C:\Users\Public\Documents\{place_name\}`

Set your Google Earth Engine project in `Test\Satellite_image.py`:
```python
ee.Initialize(project='your-project-id')
```

## Troubleshooting

**"python is not recognized"** - Python is not in your system PATH. Either:
- Add Python to your PATH (recommended), or
- Use the full path to python.exe (e.g., `C:\Python312\python.exe`)

To add Python to PATH:
1. Search "Edit the system environment variables" in Start
2. Click "Environment Variables"
3. Under "System variables", find "Path" and click "Edit"
4. Click "New" and add your Python folder (e.g., `C:\Python312`)
5. Click "OK" and restart Command Prompt

## Code Grade: 80/100

See [CODE_REVIEW.md](./CODE_REVIEW.md) for detailed code review and improvement recommendations.
