from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from winvision_macro.config import AppConfig

if TYPE_CHECKING:
    from winvision_macro.actions import PyAutoGuiInputController
    from winvision_macro.runtime import VisionMacroRunner


def load_config_with_overrides(
    config_path: str,
    dry_run: bool | None = None,
    interval_seconds: float | None = None,
    max_loops: int | None = None,
    detector_backend: str | None = None,
    yolo_model_path: str | None = None,
    yolo_confidence_threshold: float | None = None,
) -> AppConfig:
    config = AppConfig.load(config_path)
    runtime_updates: dict[str, object] = {}
    detector_updates: dict[str, object] = {}
    yolo_updates: dict[str, object] = {}

    if dry_run is not None:
        runtime_updates["dry_run"] = dry_run
    if interval_seconds is not None:
        runtime_updates["interval_seconds"] = interval_seconds
    if max_loops is not None:
        runtime_updates["max_loops"] = max_loops
    if detector_backend is not None:
        detector_updates["backend"] = detector_backend
    if yolo_model_path is not None:
        yolo_updates["model_path"] = yolo_model_path
    if yolo_confidence_threshold is not None:
        yolo_updates["confidence_threshold"] = yolo_confidence_threshold

    if not runtime_updates and not detector_updates and not yolo_updates:
        return config

    next_config = config
    if runtime_updates:
        next_config = replace(next_config, runtime=replace(next_config.runtime, **runtime_updates))
    if detector_updates:
        next_config = replace(next_config, detector=replace(next_config.detector, **detector_updates))
    if yolo_updates:
        next_config = replace(next_config, yolo=replace(next_config.yolo, **yolo_updates))
    return next_config


def build_runtime_stack(
    config_path: str,
    dry_run: bool | None = None,
    interval_seconds: float | None = None,
    max_loops: int | None = None,
    detector_backend: str | None = None,
    yolo_model_path: str | None = None,
    yolo_confidence_threshold: float | None = None,
    yolo_labels: list[str] | None = None,
) -> tuple[AppConfig, VisionMacroRunner, PyAutoGuiInputController]:
    from winvision_macro.actions import PyAutoGuiInputController
    from winvision_macro.capture import PyAutoGuiFrameSource
    from winvision_macro.runtime import VisionMacroRunner
    from winvision_macro.vision import build_detector

    config = load_config_with_overrides(
        config_path=config_path,
        dry_run=dry_run,
        interval_seconds=interval_seconds,
        max_loops=max_loops,
        detector_backend=detector_backend,
        yolo_model_path=yolo_model_path,
        yolo_confidence_threshold=yolo_confidence_threshold,
    )
    frame_source = PyAutoGuiFrameSource(config.capture_region)
    detector = build_detector(config, yolo_labels=yolo_labels)
    controller = PyAutoGuiInputController(dry_run=config.runtime.dry_run)
    runner = VisionMacroRunner(
        frame_source=frame_source,
        detector=detector,
        controller=controller,
        interval_seconds=config.runtime.interval_seconds,
    )
    return config, runner, controller
