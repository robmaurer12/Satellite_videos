# Code Review: Satellite Videos

## Grade: 68/100

The code works and is functional for personal use. Main issues are around code organization and maintainability.

---

## Issues Found

### High Priority
1. **No error handling** - Scripts lack try/except blocks for file I/O, network requests, and API calls
2. **Module-level execution** - All code runs at import time (`Satellite_video.py:37`, `Satellite_image.py:107`, `Video_thumbnail.py:38`). Makes scripts hard to import/test/reuse
3. **Blocking `getInfo()` calls** - Uses synchronous `getInfo()` calls in `Satellite_image.py:152,159` which freeze the GUI

### Medium Priority
4. **Duplicate code** - `get_user_inputs()` is duplicated in all 4 scripts - should be a shared module
5. **Empty button handlers** - `main.py:20-21` have empty script paths but buttons aren't disabled
6. **Bare except clause** - `Video_thumbnail.py:43-47` catches all exceptions without logging
7. **Duplicate variable assignment** - `Video_thumbnail.py:58` reassigns `draw` unnecessarily
8. **Variable name confusion** - `lat_left`, `lat_right` used for top/bottom bounds in `Satellite_image.py:51-65`

### Low Priority
9. **No type hints** - Beyond basic annotations, missing type hints throughout
10. **Magic numbers** - Frame durations, resolutions could be constants
11. **High DPI setting** - `Satellite_image.py:192` uses 400 DPI unnecessarily large

---

## Recommendations

1. **Create a shared `utils/` module** with common functions (`get_user_inputs()`)
2. **Wrap main logic in functions** with `if __name__ == "__main__"` guards
3. **Add proper error handling** with try/except and user-friendly messages
4. **Disable or implement empty buttons** in main.py
5. **Reduce image DPI** to 150-200 for typical use
6. **Add logging** instead of print statements

---

## What's Good

- Works as intended for personal use
- Clean GUI layout
- Good use of PIL/OpenCV for image processing
- Proper video encoding with cv2.VideoWriter
- Handy map popup feature for coordinate selection
