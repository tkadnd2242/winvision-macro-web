from __future__ import annotations

import base64

from winvision_macro.config import ScreenRegion
from winvision_macro.interfaces import Detection, FrameArray


def _load_cv2():
    try:
        import cv2  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "opencv-python is not installed. Install dependencies with 'pip install -r requirements.txt'."
        ) from exc
    return cv2


def build_preview_payload(
    frame: FrameArray,
    detections: list[Detection],
    capture_region: ScreenRegion,
    max_width: int = 960,
) -> dict[str, object]:
    cv2 = _load_cv2()
    canvas = frame.copy()

    for index, item in enumerate(detections[:8]):
        left = max(0, item.box.left - capture_region.left)
        top = max(0, item.box.top - capture_region.top)
        right = min(canvas.shape[1] - 1, left + item.box.width)
        bottom = min(canvas.shape[0] - 1, top + item.box.height)
        color = (60, 230, 170) if index == 0 else (255, 190, 90)

        cv2.rectangle(canvas, (left, top), (right, bottom), color, 2)
        label = f"{item.name} {item.score:.2f}"
        label_y = top - 10 if top > 24 else top + 22
        cv2.putText(
            canvas,
            label,
            (left, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )
        center_x = left + item.box.width // 2
        center_y = top + item.box.height // 2
        cv2.circle(canvas, (center_x, center_y), 4, color, -1)

    title = f"detections: {len(detections)}"
    cv2.putText(
        canvas,
        title,
        (14, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (220, 240, 255),
        2,
        cv2.LINE_AA,
    )

    if canvas.shape[1] > max_width:
        scale = max_width / float(canvas.shape[1])
        new_size = (int(canvas.shape[1] * scale), int(canvas.shape[0] * scale))
        canvas = cv2.resize(canvas, new_size, interpolation=cv2.INTER_AREA)

    ok, encoded = cv2.imencode(".jpg", canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise RuntimeError("Failed to encode preview image.")

    image_data = "data:image/jpeg;base64," + base64.b64encode(encoded.tobytes()).decode("ascii")
    items = [
        {
            "name": item.name,
            "score": round(item.score, 4),
            "center": item.box.center,
            "action": item.action.type,
        }
        for item in detections[:8]
    ]
    return {
        "image_data": image_data,
        "detection_count": len(detections),
        "detections": items,
        "image_width": int(canvas.shape[1]),
        "image_height": int(canvas.shape[0]),
    }
