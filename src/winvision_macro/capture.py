from __future__ import annotations

from dataclasses import dataclass

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


@dataclass
class PyAutoGuiFrameSource:
    region: ScreenRegion

    def capture(self) -> np.ndarray:
        pyautogui = _load_pyautogui()
        screenshot = pyautogui.screenshot(region=self.region.as_tuple())
        rgb = np.array(screenshot.convert("RGB"))
        return rgb[:, :, ::-1].copy()
