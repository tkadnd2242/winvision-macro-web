import tempfile
import unittest
from pathlib import Path

from winvision_macro.calibration import default_template_path, slugify_template_name
from winvision_macro.bootstrap import load_config_with_overrides
from winvision_macro.config import (
    ActionConfig,
    AppConfig,
    ScreenRegion,
    TemplateConfig,
    update_capture_region,
    upsert_template,
    write_sample_config,
)
from winvision_macro.web_control import WebControlService, _render_page


class ConfigTests(unittest.TestCase):
    def test_sample_config_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "sample.json"
            write_sample_config(config_path)
            config = AppConfig.load(config_path)

        self.assertEqual(1280, config.capture_region.width)
        self.assertTrue(config.runtime.dry_run)
        self.assertEqual("template", config.detector.backend)
        self.assertEqual("models/best.pt", config.yolo.model_path)
        self.assertEqual(3, len(config.yolo.targets))
        self.assertEqual(3, len(config.templates))
        self.assertEqual("click_center", config.templates[0].action.type)

    def test_runtime_overrides_are_applied_without_mutating_file_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "sample.json"
            write_sample_config(config_path)

            overridden = load_config_with_overrides(
                str(config_path),
                dry_run=False,
                interval_seconds=0.7,
                max_loops=15,
                detector_backend="yolo",
                yolo_model_path="models/custom.pt",
                yolo_confidence_threshold=0.77,
            )
            original = AppConfig.load(config_path)

        self.assertFalse(overridden.runtime.dry_run)
        self.assertEqual(0.7, overridden.runtime.interval_seconds)
        self.assertEqual(15, overridden.runtime.max_loops)
        self.assertEqual("yolo", overridden.detector.backend)
        self.assertEqual("models/custom.pt", overridden.yolo.model_path)
        self.assertEqual(0.77, overridden.yolo.confidence_threshold)
        self.assertTrue(original.runtime.dry_run)
        self.assertEqual(0.35, original.runtime.interval_seconds)
        self.assertEqual("template", original.detector.backend)

    def test_multi_step_actions_and_priority_round_trip(self) -> None:
        raw = {
            "capture_region": {"left": 0, "top": 0, "width": 800, "height": 600},
            "templates": [
                {
                    "name": "confirm_button",
                    "path": "templates/confirm_button.png",
                    "threshold": 0.95,
                    "cooldown_seconds": 1.0,
                    "priority": 20,
                    "actions": [
                        {"type": "move_center", "duration_seconds": 0.05},
                        {"type": "double_click_center", "post_delay_seconds": 0.1},
                        {"type": "hotkey", "keys": ["ctrl", "1"]},
                    ],
                }
            ],
        }

        config = AppConfig.from_dict(raw)
        template = config.templates[0]

        self.assertEqual(20, template.priority)
        self.assertEqual("move_center", template.action.type)
        self.assertEqual(3, len(template.actions))
        self.assertEqual("double_click_center", template.actions[1].type)
        self.assertEqual(["ctrl", "1"], template.actions[2].keys)
        encoded = config.to_dict()
        self.assertEqual(20, encoded["templates"][0]["priority"])
        self.assertEqual(3, len(encoded["templates"][0]["actions"]))

    def test_web_page_mentions_preview_endpoint(self) -> None:
        html = _render_page("configs/default.json")

        self.assertIn("Live Preview", html)
        self.assertIn("/api/preview", html)
        self.assertIn("auto_preview", html)
        self.assertIn("detector_backend", html)
        self.assertIn("yolo_model_path", html)
        self.assertIn("Calibration Studio", html)
        self.assertIn("/api/calibration/capture", html)
        self.assertIn("/api/calibration/save-template", html)
        self.assertIn("template_name", html)
        self.assertIn("Safety Lock", html)
        self.assertIn("/api/config-summary", html)
        self.assertIn("/api/live/arm", html)
        self.assertIn("frame_image_path", html)

    def test_capture_region_and_template_updates_persist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "sample.json"
            write_sample_config(config_path)

            update_capture_region(
                config_path,
                ScreenRegion(left=150, top=200, width=960, height=540),
            )
            upsert_template(
                config_path,
                TemplateConfig(
                    name="confirm_button",
                    path="templates/confirm_button_v2.png",
                    threshold=0.97,
                    cooldown_seconds=1.25,
                    action=ActionConfig(type="double_click_center"),
                ),
            )
            config = AppConfig.load(config_path)

        self.assertEqual(150, config.capture_region.left)
        self.assertEqual(540, config.capture_region.height)
        self.assertEqual(3, len(config.templates))
        confirm = next(item for item in config.templates if item.name == "confirm_button")
        self.assertEqual("templates/confirm_button_v2.png", confirm.path)
        self.assertEqual(0.97, confirm.threshold)
        self.assertEqual("double_click_center", confirm.action.type)

    def test_template_path_slugify_defaults(self) -> None:
        self.assertEqual("boss_hp_bar", slugify_template_name("Boss HP Bar"))
        self.assertEqual("templates/boss_hp_bar.png", default_template_path("Boss HP Bar"))

    def test_image_file_frame_source_reads_npy_and_returns_copy(self) -> None:
        try:
            import numpy as np
            from winvision_macro.capture import ImageFileFrameSource
        except ModuleNotFoundError:
            self.skipTest("numpy is not installed in this environment")

        with tempfile.TemporaryDirectory() as temp_dir:
            frame_path = Path(temp_dir) / "frame.npy"
            source_frame = np.arange(3 * 4 * 3, dtype=np.uint8).reshape((3, 4, 3))
            np.save(frame_path, source_frame)
            source = ImageFileFrameSource(str(frame_path))

            first = source.capture()
            second = source.capture()

        self.assertTrue(np.array_equal(source_frame, first))
        self.assertTrue(np.array_equal(source_frame, second))
        first[0, 0, 0] = 255
        self.assertNotEqual(first[0, 0, 0], second[0, 0, 0])

    def test_web_control_service_safety_lock_and_config_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "sample.json"
            write_sample_config(config_path)
            service = WebControlService(default_config_path=str(config_path))
            fake_time = [100.0]
            service.state.time_func = lambda: fake_time[0]

            summary = service.config_summary(str(config_path))
            self.assertEqual(3, summary["template_count"])
            self.assertEqual(3, summary["yolo_target_count"])
            self.assertFalse(service.safety_status()["live_input_armed"])

            with self.assertRaises(RuntimeError):
                service.ensure_live_allowed(dry_run=False)

            armed = service.arm_live_input("ARM LIVE INPUT", minutes=1.0)
            self.assertTrue(armed["live_input_armed"])
            self.assertGreater(armed["live_input_seconds_left"], 0)

            service.ensure_live_allowed(dry_run=False)
            fake_time[0] += 61.0
            self.assertFalse(service.safety_status()["live_input_armed"])


if __name__ == "__main__":
    unittest.main()
