from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from pathlib import Path

from winvision_macro.config import ScreenRegion
from winvision_macro.interfaces import FrameArray


def _load_cv2():
    try:
        import cv2  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "opencv-python is not installed. Install dependencies with 'pip install -r requirements.txt'."
        ) from exc
    return cv2


@dataclass(frozen=True)
class CalibrationSelection:
    left: int
    top: int
    width: int
    height: int

    def as_region(self) -> ScreenRegion:
        if self.width <= 0 or self.height <= 0:
            raise RuntimeError("Selection width and height must be greater than zero.")
        return ScreenRegion(
            left=int(self.left),
            top=int(self.top),
            width=int(self.width),
            height=int(self.height),
        )


def build_calibration_capture_payload(
    frame: FrameArray,
    max_width: int = 1440,
) -> dict[str, object]:
    cv2 = _load_cv2()
    source_height = int(frame.shape[0])
    source_width = int(frame.shape[1])
    canvas = frame.copy()

    if canvas.shape[1] > max_width:
        scale = max_width / float(canvas.shape[1])
        new_size = (int(canvas.shape[1] * scale), int(canvas.shape[0] * scale))
        canvas = cv2.resize(canvas, new_size, interpolation=cv2.INTER_AREA)

    ok, encoded = cv2.imencode(".jpg", canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    if not ok:
        raise RuntimeError("Failed to encode calibration image.")

    return {
        "image_data": "data:image/jpeg;base64," + base64.b64encode(encoded.tobytes()).decode("ascii"),
        "image_width": int(canvas.shape[1]),
        "image_height": int(canvas.shape[0]),
        "source_width": source_width,
        "source_height": source_height,
    }


def crop_frame(frame: FrameArray, region: ScreenRegion) -> FrameArray:
    max_height = int(frame.shape[0])
    max_width = int(frame.shape[1])
    left = max(0, min(region.left, max_width - 1))
    top = max(0, min(region.top, max_height - 1))
    right = max(left + 1, min(region.left + region.width, max_width))
    bottom = max(top + 1, min(region.top + region.height, max_height))

    if right <= left or bottom <= top:
        raise RuntimeError("Selection is outside of the captured desktop image.")
    return frame[top:bottom, left:right].copy()


def slugify_template_name(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return slug.strip("_")


def default_template_path(template_name: str) -> str:
    slug = slugify_template_name(template_name) or "template"
    return f"templates/{slug}.png"


def save_template_crop(frame: FrameArray, region: ScreenRegion, template_path: str | Path) -> Path:
    cv2 = _load_cv2()
    crop = crop_frame(frame, region)
    destination = Path(template_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(destination), crop)
    if not ok:
        raise RuntimeError(f"Failed to write template image: {destination}")
    return destination
