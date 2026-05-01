from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from winvision_macro.config import ActionConfig, AppConfig, ScreenRegion, TemplateConfig, YoloConfig
from winvision_macro.interfaces import ActionSpec, Detection, MatchBox


def _load_cv2():
    try:
        import cv2  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "opencv-python is not installed. Install dependencies with 'pip install -r requirements.txt'."
        ) from exc
    return cv2


@dataclass
class TemplateMatchDetector:
    templates: list[TemplateConfig]
    region: ScreenRegion

    def __post_init__(self) -> None:
        self._cv2 = _load_cv2()
        self._cache: dict[str, np.ndarray] = {}

    def detect(self, frame: np.ndarray) -> list[Detection]:
        results: list[Detection] = []
        for item in self.templates:
            template = self._load_template(item.path)
            if frame.shape[0] < template.shape[0] or frame.shape[1] < template.shape[1]:
                continue

            matched = self._cv2.matchTemplate(frame, template, self._cv2.TM_CCOEFF_NORMED)
            _min_val, max_val, _min_loc, max_loc = self._cv2.minMaxLoc(matched)
            score = float(max_val)
            if score < item.threshold:
                continue

            width = int(template.shape[1])
            height = int(template.shape[0])
            left = int(max_loc[0] + self.region.left)
            top = int(max_loc[1] + self.region.top)
            results.append(
                Detection(
                    name=item.name,
                    score=score,
                    box=MatchBox(left=left, top=top, width=width, height=height),
                    actions=_build_action_specs(item.resolved_actions()),
                    cooldown_seconds=item.cooldown_seconds,
                    priority=item.priority,
                )
            )

        results.sort(key=lambda item: (item.priority, item.score), reverse=True)
        return results

    def _load_template(self, path: str) -> np.ndarray:
        cached = self._cache.get(path)
        if cached is not None:
            return cached

        file_path = Path(path)
        template = self._cv2.imread(str(file_path), self._cv2.IMREAD_COLOR)
        if template is None:
            raise RuntimeError(f"Template image could not be read: {file_path}")
        self._cache[path] = template
        return template


@dataclass
class YoloDetector:
    region: ScreenRegion
    config: YoloConfig
    label_filter: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        try:
            from ultralytics import YOLO  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "YOLO mode needs 'ultralytics'. Install it with 'pip install -r requirements-yolo.txt'."
            ) from exc

        self._model = YOLO(self.config.model_path)

    def detect(self, frame: np.ndarray) -> list[Detection]:
        results = self._model.predict(
            source=frame,
            conf=self.config.confidence_threshold,
            iou=self.config.iou_threshold,
            device=self.config.device,
            verbose=False,
        )
        if not results:
            return []

        result = results[0]
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return []

        names = getattr(result, "names", {})
        target_map = {item.label: item for item in self.config.targets}
        detections: list[Detection] = []

        for box in boxes:
            class_index = int(box.cls[0].item())
            label = str(names.get(class_index, class_index))
            if self.label_filter and label not in self.label_filter:
                continue

            target = target_map.get(label)
            if target_map and target is None:
                continue

            score = float(box.conf[0].item())
            if target is not None and score < target.min_confidence:
                continue

            x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]
            width = max(1, x2 - x1)
            height = max(1, y2 - y1)
            action = target.action if target is not None else None
            cooldown = target.cooldown_seconds if target is not None else 0.0
            detections.append(
                Detection(
                    name=label,
                    score=score,
                    box=MatchBox(
                        left=self.region.left + x1,
                        top=self.region.top + y1,
                        width=width,
                        height=height,
                    ),
                    actions=_build_action_specs(
                        target.resolved_actions() if target is not None else [ActionConfig(type="click_center")]
                    ),
                    cooldown_seconds=cooldown,
                    priority=target.priority if target is not None else 0,
                )
            )

        detections.sort(key=lambda item: (item.priority, item.score), reverse=True)
        return detections


def build_detector(config: AppConfig, yolo_labels: list[str] | None = None):
    backend = config.detector.backend.strip().lower()
    if backend == "template":
        return TemplateMatchDetector(config.templates, config.capture_region)
    if backend == "yolo":
        label_filter = {
            item.strip()
            for item in (yolo_labels or [])
            if item is not None and item.strip()
        }
        return YoloDetector(
            region=config.capture_region,
            config=config.yolo,
            label_filter=label_filter,
        )
    raise RuntimeError(f"Unsupported detector backend: {config.detector.backend}")


def _build_action_specs(actions: list[ActionConfig]) -> tuple[ActionSpec, ...]:
    return tuple(
        ActionSpec(
            type=item.type,
            key=item.key,
            keys=tuple(item.keys),
            text=item.text,
            button=item.button,
            repeat=item.repeat,
            interval_seconds=item.interval_seconds,
            duration_seconds=item.duration_seconds,
            offset_x=item.offset_x,
            offset_y=item.offset_y,
            scroll_amount=item.scroll_amount,
            post_delay_seconds=item.post_delay_seconds,
        )
        for item in actions
    )
