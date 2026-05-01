@echo off
setlocal
cd /d %~dp0

if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Run setup-windows.bat first.
  exit /b 1
)

set PYTHONPATH=src
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json
