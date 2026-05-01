from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from winvision_macro.interfaces import Detection, Detector, FrameSource, InputController


LoopCallback = Callable[[int, list[Detection]], None]
StopCallback = Callable[[], bool]


@dataclass
class VisionMacroRunner:
    frame_source: FrameSource
    detector: Detector
    controller: InputController
    interval_seconds: float = 0.35
    _cooldowns: dict[str, float] = field(default_factory=dict)

    def run(
        self,
        max_loops: int = 0,
        on_loop: LoopCallback | None = None,
        should_stop: StopCallback | None = None,
    ) -> None:
        loop_index = 0
        while max_loops <= 0 or loop_index < max_loops:
            if should_stop is not None and should_stop():
                break
            loop_index += 1
            frame = self.frame_source.capture()
            detections = self.detector.detect(frame)

            executable = self._pick_executable_detection(detections)
            if executable is not None:
                self.controller.perform(executable)
                self._cooldowns[executable.name] = time.time() + executable.cooldown_seconds

            if on_loop is not None:
                on_loop(loop_index, detections)

            if should_stop is not None and should_stop():
                break

            time.sleep(self.interval_seconds)

    def run_once(self) -> list[Detection]:
        frame = self.frame_source.capture()
        detections = self.detector.detect(frame)
        executable = self._pick_executable_detection(detections)
        if executable is not None:
            self.controller.perform(executable)
            self._cooldowns[executable.name] = time.time() + executable.cooldown_seconds
        return detections

    def _pick_executable_detection(self, detections: list[Detection]) -> Detection | None:
        now = time.time()
        ranked = sorted(detections, key=lambda item: (item.priority, item.score), reverse=True)
        for item in ranked:
            if self._cooldowns.get(item.name, 0.0) <= now:
                return item
        return None
