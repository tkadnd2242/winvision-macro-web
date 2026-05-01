from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScreenRegion:
    left: int
    top: int
    width: int
    height: int

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.width, self.height)


@dataclass(frozen=True)
class ActionConfig:
    type: str
    key: str | None = None


@dataclass(frozen=True)
class TemplateConfig:
    name: str
    path: str
    threshold: float = 0.9
    cooldown_seconds: float = 0.0
    action: ActionConfig = field(default_factory=lambda: ActionConfig(type="click_center"))


@dataclass(frozen=True)
class RuntimeConfig:
    interval_seconds: float = 0.35
    dry_run: bool = True
    max_loops: int = 0


@dataclass(frozen=True)
class DetectorConfig:
    backend: str = "template"


@dataclass(frozen=True)
class YoloTargetConfig:
    label: str
    min_confidence: float = 0.5
    cooldown_seconds: float = 0.0
    action: ActionConfig = field(default_factory=lambda: ActionConfig(type="click_center"))


@dataclass(frozen=True)
class YoloConfig:
    model_path: str = "models/best.pt"
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    device: str | None = None
    targets: list[YoloTargetConfig] = field(default_factory=list)


@dataclass(frozen=True)
class AppConfig:
    capture_region: ScreenRegion
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    yolo: YoloConfig = field(default_factory=YoloConfig)
    templates: list[TemplateConfig] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> "AppConfig":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "AppConfig":
        region = ScreenRegion(**raw["capture_region"])
        runtime = RuntimeConfig(**raw.get("runtime", {}))
        detector = DetectorConfig(**raw.get("detector", {}))
        yolo_raw = raw.get("yolo", {})
        yolo = YoloConfig(
            model_path=yolo_raw.get("model_path", "models/best.pt"),
            confidence_threshold=yolo_raw.get("confidence_threshold", 0.5),
            iou_threshold=yolo_raw.get("iou_threshold", 0.45),
            device=yolo_raw.get("device"),
            targets=[
                YoloTargetConfig(
                    label=item["label"],
                    min_confidence=item.get("min_confidence", 0.5),
                    cooldown_seconds=item.get("cooldown_seconds", 0.0),
                    action=ActionConfig(**item.get("action", {"type": "click_center"})),
                )
                for item in yolo_raw.get("targets", [])
            ],
        )

        templates = [
            TemplateConfig(
                name=item["name"],
                path=item["path"],
                threshold=item.get("threshold", 0.9),
                cooldown_seconds=item.get("cooldown_seconds", 0.0),
                action=ActionConfig(**item.get("action", {"type": "click_center"})),
            )
            for item in raw.get("templates", [])
        ]

        return cls(
            capture_region=region,
            runtime=runtime,
            detector=detector,
            yolo=yolo,
            templates=templates,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "capture_region": {
                "left": self.capture_region.left,
                "top": self.capture_region.top,
                "width": self.capture_region.width,
                "height": self.capture_region.height,
            },
            "runtime": {
                "interval_seconds": self.runtime.interval_seconds,
                "dry_run": self.runtime.dry_run,
                "max_loops": self.runtime.max_loops,
            },
            "detector": {
                "backend": self.detector.backend,
            },
            "yolo": {
                "model_path": self.yolo.model_path,
                "confidence_threshold": self.yolo.confidence_threshold,
                "iou_threshold": self.yolo.iou_threshold,
                "device": self.yolo.device,
                "targets": [
                    {
                        "label": item.label,
                        "min_confidence": item.min_confidence,
                        "cooldown_seconds": item.cooldown_seconds,
                        "action": {
                            "type": item.action.type,
                            "key": item.action.key,
                        },
                    }
                    for item in self.yolo.targets
                ],
            },
            "templates": [
                {
                    "name": item.name,
                    "path": item.path,
                    "threshold": item.threshold,
                    "cooldown_seconds": item.cooldown_seconds,
                    "action": {
                        "type": item.action.type,
                        "key": item.action.key,
                    },
                }
                for item in self.templates
            ],
        }


def write_sample_config(path: str | Path) -> Path:
    config = AppConfig(
        capture_region=ScreenRegion(left=0, top=0, width=1280, height=720),
        runtime=RuntimeConfig(interval_seconds=0.35, dry_run=True, max_loops=200),
        detector=DetectorConfig(backend="template"),
        yolo=YoloConfig(
            model_path="models/best.pt",
            confidence_threshold=0.5,
            iou_threshold=0.45,
            device=None,
            targets=[
                YoloTargetConfig(
                    label="enemy",
                    min_confidence=0.55,
                    cooldown_seconds=0.3,
                    action=ActionConfig(type="click_center"),
                ),
                YoloTargetConfig(
                    label="confirm",
                    min_confidence=0.7,
                    cooldown_seconds=0.8,
                    action=ActionConfig(type="double_click_center"),
                ),
                YoloTargetConfig(
                    label="skill_ready",
                    min_confidence=0.65,
                    cooldown_seconds=1.2,
                    action=ActionConfig(type="press_key", key="1"),
                ),
            ],
        ),
        templates=[
            TemplateConfig(
                name="target_button",
                path="templates/target_button.png",
                threshold=0.92,
                cooldown_seconds=0.75,
                action=ActionConfig(type="click_center"),
            ),
            TemplateConfig(
                name="confirm_button",
                path="templates/confirm_button.png",
                threshold=0.94,
                cooldown_seconds=1.0,
                action=ActionConfig(type="double_click_center"),
            ),
            TemplateConfig(
                name="skill_ready",
                path="templates/skill_ready.png",
                threshold=0.90,
                cooldown_seconds=2.0,
                action=ActionConfig(type="press_key", key="1"),
            ),
        ],
    )
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    return destination
