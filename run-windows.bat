@echo off
setlocal
cd /d %~dp0

if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Run setup-windows.bat first.
  exit /b 1
)

set PYTHONPATH=src
echo Starting local web dashboard at http://127.0.0.1:8765
.venv\Scripts\python.exe -m winvision_macro --mode web --config configs/default.json --host 127.0.0.1 --port 8765
