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
- static frame image testing from a saved screenshot or `.npy` frame file
- live input safety lock before real mouse or keyboard control
- a Korean step-by-step run guide in `RUN_GUIDE_KO.md`
- a Korean manual test checklist in `TEST_CHECKLIST_KO.md`
- a Korean per-file guide in `FILE_GUIDE_KO.md`

## Project layout

- `src/winvision_macro/config.py`: config dataclasses and JSON loader
- `src/winvision_macro/interfaces.py`: shared protocols and data models
- `src/winvision_macro/capture.py`: screen capture backend using `pyautogui`
- `src/winvision_macro/calibration.py`: desktop capture export, crop save, and calibration helpers
- `src/winvision_macro/vision.py`: OpenCV template matching detector
- `requirements-yolo.txt`: optional YOLO dependency install list
- `src/winvision_macro/actions.py`: keyboard and mouse action executor
- `src/winvision_macro/runtime.py`: main automation loop
- `src/winvision_macro/web_control.py`: local browser control panel
- `src/winvision_macro/main.py`: CLI entrypoint
- `configs/default.json`: sample automation config
- `RUN_GUIDE_KO.md`: Korean setup and execution guide
- `TEST_CHECKLIST_KO.md`: Korean manual test checklist
- `FILE_GUIDE_KO.md`: Korean file-by-file guide
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
3. Rank matches by priority and confidence
4. Execute the mapped action for the top match
5. Respect dry-run, action sequences, and per-target cooldown settings
6. Surface status and logs in the browser dashboard
7. Render a preview frame with detection boxes for calibration

## Supported macro actions

Each template or YOLO target can use a single `action` or a multi-step `actions` list.

- `click_center`
- `double_click_center`
- `right_click_center`
- `move_center`
- `press_key`
- `hotkey`
- `type_text`
- `scroll`
- `wait`

Useful action fields include `priority`, `repeat`, `interval_seconds`, `duration_seconds`, `offset_x`, `offset_y`, and `post_delay_seconds`.

## Safe testing

Use dry-run first so the runtime only logs what it would do.

```bash
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json --once --dry-run
```

To run a short live loop after validation:

```bash
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json --max-loops 10 --live
```

To test detections against a saved screenshot instead of the live desktop:

```bash
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json --once --dry-run --frame-image captures/sample_screen.png
```

You can also inspect the current config quickly:

```bash
.venv\Scripts\python.exe -m winvision_macro --config configs/default.json --print-config-summary
```

## Automated tests

You can validate config parsing, action execution, cooldown behavior, and macro priority logic with:

```bash
set PYTHONPATH=src
python -m unittest discover -s tests
```

## Next steps

1. Place real template images in `templates/`
2. If you use YOLO, place your model file in `models/`
3. Update `configs/default.json` with your screen region and actions
4. Start from the web dashboard in dry-run mode first
5. Switch the detector selector to `YOLO` and tune confidence plus allowed labels
6. Add a dedicated deep learning model endpoint or Windows-specific UI only if the browser control panel becomes limiting

## Calibration flow

1. Open the browser dashboard and click `Capture Desktop`
2. Drag over the captured image to select the game window region
3. Click `Apply Region To Config` to write that rectangle into `capture_region`
4. Drag a smaller UI element from the same capture and use `Save Template Crop`
5. Keep `Save template metadata into the config file` enabled if you want the template entry added automatically
6. Return to `Live Preview` and confirm detections before turning off `dry_run`

## Web testing helpers

- `Safety Lock`: live input stays blocked until you type `ARM LIVE INPUT`
- `Config Snapshot`: shows current templates, priorities, and YOLO targets from the config
- `Frame Image`: lets you point the dashboard at a saved screenshot for repeatable dry-run tests
