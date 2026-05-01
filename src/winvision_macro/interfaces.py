from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

    FrameArray = np.ndarray
else:
    FrameArray = Any


@dataclass(frozen=True)
class MatchBox:
    left: int
    top: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        return (self.left + self.width // 2, self.top + self.height // 2)


@dataclass(frozen=True)
class ActionSpec:
    type: str
    key: str | None = None
    keys: tuple[str, ...] = ()
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
class Detection:
    name: str
    score: float
    box: MatchBox
    actions: tuple[ActionSpec, ...]
    cooldown_seconds: float = 0.0
    priority: int = 0

    @property
    def action(self) -> ActionSpec:
        return self.actions[0]


class FrameSource(Protocol):
    def capture(self) -> FrameArray:
        """Return a BGR image."""


class Detector(Protocol):
    def detect(self, frame: FrameArray) -> list[Detection]:
        """Return detections for the current frame."""


class InputController(Protocol):
    def perform(self, detection: Detection) -> None:
        """Execute the action mapped to a detection."""
