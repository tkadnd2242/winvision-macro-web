import unittest

from winvision_macro.actions import PyAutoGuiInputController
from winvision_macro.interfaces import ActionSpec, Detection, MatchBox
from winvision_macro.runtime import VisionMacroRunner


class FakePyAutoGui:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def click(
        self,
        x: int | None = None,
        y: int | None = None,
        clicks: int = 1,
        interval: float = 0.0,
        button: str = "left",
        duration: float = 0.0,
    ) -> None:
        self.calls.append(("click", x, y, clicks, interval, button, duration))

    def doubleClick(
        self,
        x: int | None = None,
        y: int | None = None,
        interval: float = 0.0,
        button: str = "left",
        duration: float = 0.0,
    ) -> None:
        self.calls.append(("doubleClick", x, y, interval, button, duration))

    def moveTo(self, x: int, y: int, duration: float = 0.0) -> None:
        self.calls.append(("moveTo", x, y, duration))

    def press(self, key: str, presses: int = 1, interval: float = 0.0) -> None:
        self.calls.append(("press", key, presses, interval))

    def hotkey(self, *keys: str, interval: float = 0.0) -> None:
        self.calls.append(("hotkey", keys, interval))

    def write(self, message: str, interval: float = 0.0) -> None:
        self.calls.append(("write", message, interval))

    def scroll(self, clicks: int, x: int | None = None, y: int | None = None) -> None:
        self.calls.append(("scroll", clicks, x, y))


class FakeFrameSource:
    def __init__(self) -> None:
        self.capture_count = 0

    def capture(self):
        self.capture_count += 1
        return object()


class FakeDetector:
    def __init__(self, detections: list[Detection]) -> None:
        self.detections = detections
        self.detect_count = 0

    def detect(self, frame):
        self.detect_count += 1
        return list(self.detections)


class MacroRuntimeTests(unittest.TestCase):
    def test_controller_executes_multi_step_macro_sequence(self) -> None:
        backend = FakePyAutoGui()
        sleeps: list[float] = []
        controller = PyAutoGuiInputController(
            dry_run=False,
            backend=backend,
            sleeper=sleeps.append,
        )
        detection = Detection(
            name="confirm_button",
            score=0.98,
            box=MatchBox(left=100, top=200, width=40, height=20),
            actions=(
                ActionSpec(type="move_center", duration_seconds=0.05),
                ActionSpec(type="click_center", offset_x=5, offset_y=-2, repeat=2, post_delay_seconds=0.1),
                ActionSpec(type="press_key", key="1", repeat=2, interval_seconds=0.03),
                ActionSpec(type="hotkey", keys=("ctrl", "shift", "s")),
                ActionSpec(type="type_text", text="/dance", interval_seconds=0.02),
                ActionSpec(type="scroll", scroll_amount=-400),
                ActionSpec(type="wait", duration_seconds=0.25),
            ),
            cooldown_seconds=1.0,
            priority=10,
        )

        controller.perform(detection)

        self.assertEqual(
            [
                ("moveTo", 120, 210, 0.05),
                ("click", 125, 208, 2, 0.0, "left", 0.0),
                ("press", "1", 2, 0.03),
                ("hotkey", ("ctrl", "shift", "s"), 0.0),
                ("write", "/dance", 0.02),
                ("scroll", -400, 120, 210),
            ],
            backend.calls,
        )
        self.assertEqual([0.1, 0.25], sleeps)
        self.assertIn("step=2 click_center:confirm_button@125,208:button=left:repeat=2", controller.action_log)
        self.assertIn("step=7 wait:0.25:confirm_button", controller.action_log)

    def test_runner_respects_detection_cooldown(self) -> None:
        detection = Detection(
            name="target_button",
            score=0.9,
            box=MatchBox(left=10, top=10, width=30, height=30),
            actions=(ActionSpec(type="click_center"),),
            cooldown_seconds=60.0,
            priority=1,
        )
        frame_source = FakeFrameSource()
        detector = FakeDetector([detection])
        controller = PyAutoGuiInputController(dry_run=True)
        runner = VisionMacroRunner(
            frame_source=frame_source,
            detector=detector,
            controller=controller,
            interval_seconds=0.0,
        )

        first = runner.run_once()
        second = runner.run_once()

        self.assertEqual(1, len(first))
        self.assertEqual(1, len(second))
        self.assertEqual(2, frame_source.capture_count)
        self.assertEqual(2, detector.detect_count)
        self.assertEqual(1, len(controller.action_log))
        self.assertIn("click_center:target_button", controller.action_log[0])

    def test_runner_prefers_higher_priority_even_with_lower_score(self) -> None:
        low_priority = Detection(
            name="enemy",
            score=0.99,
            box=MatchBox(left=0, top=0, width=20, height=20),
            actions=(ActionSpec(type="click_center"),),
            cooldown_seconds=0.0,
            priority=1,
        )
        high_priority = Detection(
            name="confirm_button",
            score=0.70,
            box=MatchBox(left=50, top=50, width=20, height=20),
            actions=(ActionSpec(type="double_click_center"),),
            cooldown_seconds=0.0,
            priority=50,
        )
        runner = VisionMacroRunner(
            frame_source=FakeFrameSource(),
            detector=FakeDetector([low_priority, high_priority]),
            controller=PyAutoGuiInputController(dry_run=True),
            interval_seconds=0.0,
        )

        runner.run_once()

        self.assertIn("double_click_center:confirm_button", runner.controller.action_log[0])


if __name__ == "__main__":
    unittest.main()
