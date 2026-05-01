# WinVision Macro

Windows desktop automation scaffold built with Python, OpenCV, and `pyautogui`.

This project is designed as a clean starting point for:

- screen capture from a Windows desktop region
- OpenCV-based template detection
- optional future deep learning detectors such as YOLO
- selectable detector backend between template matching and YOLO
- action execution through mouse and keyboard automation
- dry-run testing before enabling real input
- local browser dashboard for control and logs
- annotated preview image in the browser for calibration

## Project layout

- `src/winvision_macro/config.py`: config dataclasses and JSON loader
- `src/winvision_macro/interfaces.py`: shared protocols and data models
- `src/winvision_macro/capture.py`: screen capture backend using `pyautogui`
- `src/winvision_macro/vision.py`: OpenCV template matching detector
- `requirements-yolo.txt`: optional YOLO dependency install list
- `src/winvision_macro/actions.py`: keyboard and mouse action executor
- `src/winvision_macro/runtime.py`: main automation loop
- `src/winvision_macro/web_control.py`: local browser control panel
- `src/winvision_macro/main.py`: CLI entrypoint
- `configs/default.json`: sample automation config
- `templates/README.md`: template crop guidance and placeholder folder
- `models/README.md`: YOLO model placement guidance and placeholder folder
- `run-windows.bat`: start the browser dashboard
- `run-cli-windows.bat`: start the CLI loop directly
- `setup-windows.bat`: virtualenv and dependency installer

## Quick start

### Windows

```bat
setup-windows.bat
run-windows.bat
```

Then open `http://127.0.0.1:8765`.

If you want YOLO mode too:

```bat
.venv\Scripts\python.exe -m pip install -r requirements-yolo.txt
```

### Manual

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements-yolo.txt
set PYTHONPATH=src
.venv\Scripts\python.exe -m winvision_macro --write-sample-config
.venv\Scripts\python.exe -m winvision_macro --mode web --config configs/default.json --host 127.0.0.1 --port 8765
```

If you want the old terminal flow instead:

```bash
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json --once
```

## How it works

1. Capture a desktop region
2. Run either template matching or YOLO detection
3. Sort matches by confidence
4. Execute the mapped action for the top match
5. Respect dry-run and per-target cooldown settings
6. Surface status and logs in the browser dashboard
7. Render a preview frame with detection boxes for calibration

## Next steps

1. Place real template images in `templates/`
2. If you use YOLO, place your model file in `models/`
3. Update `configs/default.json` with your screen region and actions
4. Start from the web dashboard in dry-run mode first
5. Switch the detector selector to `YOLO` and tune confidence plus allowed labels
6. Add a dedicated deep learning model endpoint or Windows-specific UI only if the browser control panel becomes limiting
