from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from winvision_macro.config import ScreenRegion


def _load_pyautogui():
    try:
        import pyautogui  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "pyautogui is not installed. Install dependencies with 'pip install -r requirements.txt'."
        ) from exc
    return pyautogui


def _load_cv2():
    try:
        import cv2  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "opencv-python is not installed. Install dependencies with 'pip install -r requirements.txt'."
        ) from exc
    return cv2


@dataclass
class PyAutoGuiFrameSource:
    region: ScreenRegion

    def capture(self) -> np.ndarray:
        return capture_screen(self.region)


@dataclass
class ImageFileFrameSource:
    path: str
    _cached_frame: np.ndarray | None = None

    def capture(self) -> np.ndarray:
        if self._cached_frame is None:
            self._cached_frame = load_frame_file(self.path)
        return self._cached_frame.copy()


def capture_screen(region: ScreenRegion | None = None) -> np.ndarray:
    pyautogui = _load_pyautogui()
    screenshot = pyautogui.screenshot(region=None if region is None else region.as_tuple())
    rgb = np.array(screenshot.convert("RGB"))
    return rgb[:, :, ::-1].copy()


def load_frame_file(path: str | Path) -> np.ndarray:
    file_path = Path(path)
    if not file_path.exists():
        raise RuntimeError(f"Frame image file was not found: {file_path}")

    if file_path.suffix.lower() == ".npy":
        frame = np.load(file_path)
    else:
        cv2 = _load_cv2()
        frame = cv2.imread(str(file_path), cv2.IMREAD_COLOR)

    if frame is None:
        raise RuntimeError(f"Frame image could not be read: {file_path}")
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise RuntimeError(f"Frame image must have 3 color channels: {file_path}")
    return np.ascontiguousarray(frame)
