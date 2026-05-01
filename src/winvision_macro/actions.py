from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Protocol

from winvision_macro.interfaces import ActionSpec, Detection


class PyAutoGuiBackend(Protocol):
    def click(
        self,
        x: int | None = None,
        y: int | None = None,
        clicks: int = 1,
        interval: float = 0.0,
        button: str = "left",
        duration: float = 0.0,
    ) -> None:
        ...

    def doubleClick(
        self,
        x: int | None = None,
        y: int | None = None,
        interval: float = 0.0,
        button: str = "left",
        duration: float = 0.0,
    ) -> None:
        ...

    def moveTo(self, x: int, y: int, duration: float = 0.0) -> None:
        ...

    def press(self, key: str, presses: int = 1, interval: float = 0.0) -> None:
        ...

    def hotkey(self, *keys: str, interval: float = 0.0) -> None:
        ...

    def write(self, message: str, interval: float = 0.0) -> None:
        ...

    def scroll(self, clicks: int, x: int | None = None, y: int | None = None) -> None:
        ...


def _load_pyautogui() -> PyAutoGuiBackend:
    try:
        import pyautogui  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "pyautogui is not installed. Install dependencies with 'pip install -r requirements.txt'."
        ) from exc
    return pyautogui


@dataclass
class PyAutoGuiInputController:
    dry_run: bool = True
    action_log: list[str] = field(default_factory=list)
    backend: PyAutoGuiBackend | None = None
    sleeper: Callable[[float], None] = time.sleep

    def perform(self, detection: Detection) -> None:
        for index, action in enumerate(detection.actions, start=1):
            self._perform_action(detection, action, step_index=index)

    def _perform_action(self, detection: Detection, action: ActionSpec, step_index: int) -> None:
        center_x, center_y = detection.box.center
        target_x = center_x + action.offset_x
        target_y = center_y + action.offset_y
        action_type = action.type

        if action_type == "click_center":
            self._log(
                f"step={step_index} click_center:{detection.name}@{target_x},{target_y}"
                f":button={action.button}:repeat={action.repeat}"
            )
            if not self.dry_run:
                backend = self._backend()
                backend.click(
                    x=target_x,
                    y=target_y,
                    clicks=max(1, action.repeat),
                    interval=max(0.0, action.interval_seconds),
                    button=action.button,
                    duration=max(0.0, action.duration_seconds),
                )
            self._post_delay(action)
            return

        if action_type == "double_click_center":
            self._log(f"step={step_index} double_click_center:{detection.name}@{target_x},{target_y}")
            if not self.dry_run:
                backend = self._backend()
                backend.doubleClick(
                    x=target_x,
                    y=target_y,
                    interval=max(0.0, action.interval_seconds),
                    button=action.button,
                    duration=max(0.0, action.duration_seconds),
                )
            self._post_delay(action)
            return

        if action_type == "right_click_center":
            self._log(f"step={step_index} right_click_center:{detection.name}@{target_x},{target_y}")
            if not self.dry_run:
                backend = self._backend()
                backend.click(
                    x=target_x,
                    y=target_y,
                    clicks=max(1, action.repeat),
                    interval=max(0.0, action.interval_seconds),
                    button="right",
                    duration=max(0.0, action.duration_seconds),
                )
            self._post_delay(action)
            return

        if action_type == "move_center":
            self._log(f"step={step_index} move_center:{detection.name}@{target_x},{target_y}")
            if not self.dry_run:
                backend = self._backend()
                backend.moveTo(target_x, target_y, duration=max(0.0, action.duration_seconds))
            self._post_delay(action)
            return

        if action_type == "press_key":
            if not action.key:
                raise RuntimeError("Action 'press_key' needs a configured key.")
            self._log(
                f"step={step_index} press_key:{action.key}:{detection.name}:repeat={max(1, action.repeat)}"
            )
            if not self.dry_run:
                backend = self._backend()
                backend.press(
                    action.key,
                    presses=max(1, action.repeat),
                    interval=max(0.0, action.interval_seconds),
                )
            self._post_delay(action)
            return

        if action_type == "hotkey":
            keys = action.keys or ((action.key,) if action.key else ())
            if not keys:
                raise RuntimeError("Action 'hotkey' needs at least one key.")
            self._log(f"step={step_index} hotkey:{'+'.join(keys)}:{detection.name}")
            if not self.dry_run:
                backend = self._backend()
                backend.hotkey(*keys, interval=max(0.0, action.interval_seconds))
            self._post_delay(action)
            return

        if action_type == "type_text":
            if action.text is None:
                raise RuntimeError("Action 'type_text' needs configured text.")
            self._log(f"step={step_index} type_text:{action.text}:{detection.name}")
            if not self.dry_run:
                backend = self._backend()
                backend.write(action.text, interval=max(0.0, action.interval_seconds))
            self._post_delay(action)
            return

        if action_type == "scroll":
            self._log(f"step={step_index} scroll:{action.scroll_amount}:{detection.name}@{target_x},{target_y}")
            if not self.dry_run:
                backend = self._backend()
                backend.scroll(action.scroll_amount, x=target_x, y=target_y)
            self._post_delay(action)
            return

        if action_type == "wait":
            wait_seconds = max(action.duration_seconds, action.post_delay_seconds, action.interval_seconds)
            self._log(f"step={step_index} wait:{wait_seconds:.2f}:{detection.name}")
            if wait_seconds > 0:
                self.sleeper(wait_seconds)
            return

        raise RuntimeError(f"Unsupported action type: {action_type}")

    def _backend(self) -> PyAutoGuiBackend:
        return self.backend if self.backend is not None else _load_pyautogui()

    def _log(self, line: str) -> None:
        self.action_log.append(line)

    def _post_delay(self, action: ActionSpec) -> None:
        delay = max(0.0, action.post_delay_seconds)
        if delay > 0:
            self.sleeper(delay)
