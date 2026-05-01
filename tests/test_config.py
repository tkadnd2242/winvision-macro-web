import tempfile
import unittest
from pathlib import Path

from winvision_macro.bootstrap import load_config_with_overrides
from winvision_macro.config import AppConfig, write_sample_config
from winvision_macro.web_control import _render_page


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

    def test_web_page_mentions_preview_endpoint(self) -> None:
        html = _render_page("configs/default.json")

        self.assertIn("Live Preview", html)
        self.assertIn("/api/preview", html)
        self.assertIn("auto_preview", html)
        self.assertIn("detector_backend", html)
        self.assertIn("yolo_model_path", html)


if __name__ == "__main__":
    unittest.main()
