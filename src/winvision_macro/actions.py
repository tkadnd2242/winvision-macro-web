from __future__ import annotations

from dataclasses import dataclass, field

from winvision_macro.interfaces import Detection


def _load_pyautogui():
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

    def perform(self, detection: Detection) -> None:
        center_x, center_y = detection.box.center
        action_type = detection.action.type

        if action_type == "click_center":
            self.action_log.append(f"click_center:{detection.name}@{center_x},{center_y}")
            if not self.dry_run:
                pyautogui = _load_pyautogui()
                pyautogui.click(center_x, center_y)
            return

        if action_type == "double_click_center":
            self.action_log.append(f"double_click_center:{detection.name}@{center_x},{center_y}")
            if not self.dry_run:
                pyautogui = _load_pyautogui()
                pyautogui.doubleClick(center_x, center_y)
            return

        if action_type == "press_key":
            if not detection.action.key:
                raise RuntimeError(f"Action '{action_type}' needs a configured key.")
            self.action_log.append(f"press_key:{detection.action.key}:{detection.name}")
            if not self.dry_run:
                pyautogui = _load_pyautogui()
                pyautogui.press(detection.action.key)
            return

        raise RuntimeError(f"Unsupported action type: {action_type}")
