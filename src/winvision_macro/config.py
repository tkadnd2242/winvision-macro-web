from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
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
    keys: list[str] = field(default_factory=list)
    text: str | None = None
    button: str = "left"
    repeat: int = 1
    interval_seconds: float = 0.0
    duration_seconds: float = 0.0
    offset_x: int = 0
    offset_y: int = 0
    scroll_amount: int = 0
    post_delay_seconds: float = 0.0


@dataclass(frozen=True)
class TemplateConfig:
    name: str
    path: str
    threshold: float = 0.9
    cooldown_seconds: float = 0.0
    action: ActionConfig = field(default_factory=lambda: ActionConfig(type="click_center"))
    actions: list[ActionConfig] = field(default_factory=list)
    priority: int = 0

    def resolved_actions(self) -> list[ActionConfig]:
        return list(self.actions) if self.actions else [self.action]


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
    actions: list[ActionConfig] = field(default_factory=list)
    priority: int = 0

    def resolved_actions(self) -> list[ActionConfig]:
        return list(self.actions) if self.actions else [self.action]


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
                    action=_primary_action_from_dict(item),
                    actions=_actions_from_dict(item),
                    priority=item.get("priority", 0),
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
                action=_primary_action_from_dict(item),
                actions=_actions_from_dict(item),
                priority=item.get("priority", 0),
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
                        "priority": item.priority,
                        "action": _action_to_dict(item.action),
                        **({"actions": [_action_to_dict(action) for action in item.actions]} if len(item.actions) > 1 else {}),
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
                    "priority": item.priority,
                    "action": _action_to_dict(item.action),
                    **({"actions": [_action_to_dict(action) for action in item.actions]} if len(item.actions) > 1 else {}),
                }
                for item in self.templates
            ],
        }


def _action_from_dict(raw: dict[str, Any]) -> ActionConfig:
    return ActionConfig(
        type=raw["type"],
        key=raw.get("key"),
        keys=list(raw.get("keys", [])),
        text=raw.get("text"),
        button=raw.get("button", "left"),
        repeat=raw.get("repeat", 1),
        interval_seconds=raw.get("interval_seconds", 0.0),
        duration_seconds=raw.get("duration_seconds", 0.0),
        offset_x=raw.get("offset_x", 0),
        offset_y=raw.get("offset_y", 0),
        scroll_amount=raw.get("scroll_amount", 0),
        post_delay_seconds=raw.get("post_delay_seconds", 0.0),
    )


def _actions_from_dict(raw: dict[str, Any]) -> list[ActionConfig]:
    action_items = raw.get("actions")
    if isinstance(action_items, list) and action_items:
        return [_action_from_dict(item) for item in action_items]
    return []


def _primary_action_from_dict(raw: dict[str, Any]) -> ActionConfig:
    actions = _actions_from_dict(raw)
    if actions:
        return actions[0]
    return _action_from_dict(raw.get("action", {"type": "click_center"}))


def _action_to_dict(action: ActionConfig) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": action.type,
        "button": action.button,
        "repeat": action.repeat,
        "interval_seconds": action.interval_seconds,
        "duration_seconds": action.duration_seconds,
        "offset_x": action.offset_x,
        "offset_y": action.offset_y,
        "scroll_amount": action.scroll_amount,
        "post_delay_seconds": action.post_delay_seconds,
    }
    if action.key is not None:
        payload["key"] = action.key
    if action.keys:
        payload["keys"] = list(action.keys)
    if action.text is not None:
        payload["text"] = action.text
    return payload


def save_config(path: str | Path, config: AppConfig) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    return destination


def update_capture_region(path: str | Path, region: ScreenRegion) -> AppConfig:
    config = AppConfig.load(path)
    next_config = replace(config, capture_region=region)
    save_config(path, next_config)
    return next_config


def upsert_template(path: str | Path, template: TemplateConfig) -> AppConfig:
    config = AppConfig.load(path)
    templates: list[TemplateConfig] = []
    replaced = False
    for item in config.templates:
        if item.name == template.name:
            templates.append(template)
            replaced = True
        else:
            templates.append(item)

    if not replaced:
        templates.append(template)

    next_config = replace(config, templates=templates)
    save_config(path, next_config)
    return next_config


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
                    priority=5,
                ),
                YoloTargetConfig(
                    label="confirm",
                    min_confidence=0.7,
                    cooldown_seconds=0.8,
                    action=ActionConfig(type="move_center", duration_seconds=0.05),
                    actions=[
                        ActionConfig(type="move_center", duration_seconds=0.05),
                        ActionConfig(type="double_click_center", post_delay_seconds=0.1),
                    ],
                    priority=30,
                ),
                YoloTargetConfig(
                    label="skill_ready",
                    min_confidence=0.65,
                    cooldown_seconds=1.2,
                    action=ActionConfig(type="press_key", key="1"),
                    priority=20,
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
                priority=5,
            ),
            TemplateConfig(
                name="confirm_button",
                path="templates/confirm_button.png",
                threshold=0.94,
                cooldown_seconds=1.0,
                action=ActionConfig(type="move_center", duration_seconds=0.05),
                actions=[
                    ActionConfig(type="move_center", duration_seconds=0.05),
                    ActionConfig(type="double_click_center", post_delay_seconds=0.1),
                ],
                priority=30,
            ),
            TemplateConfig(
                name="skill_ready",
                path="templates/skill_ready.png",
                threshold=0.90,
                cooldown_seconds=2.0,
                action=ActionConfig(type="press_key", key="1"),
                priority=20,
            ),
        ],
    )
    destination = Path(path)
    return save_config(destination, config)
