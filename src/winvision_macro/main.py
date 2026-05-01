from __future__ import annotations

import argparse
import json
from pathlib import Path

from winvision_macro.bootstrap import build_runtime_stack
from winvision_macro.config import AppConfig, write_sample_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the WinVision Macro runtime.")
    parser.add_argument("--config", default="configs/default.json", help="Path to the JSON config.")
    parser.add_argument(
        "--mode",
        choices=["cli", "web"],
        default="cli",
        help="Run the direct CLI loop or the browser dashboard.",
    )
    parser.add_argument("--once", action="store_true", help="Run a single capture-detect-action cycle.")
    parser.add_argument(
        "--write-sample-config",
        action="store_true",
        help="Write a fresh sample config file and exit.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for web mode.")
    parser.add_argument("--port", type=int, default=8765, help="Port for web mode.")
    parser.add_argument(
        "--detector-backend",
        choices=["template", "yolo"],
        help="Override the detector backend from the config.",
    )
    parser.add_argument("--yolo-model-path", help="Override the YOLO model path from the config.")
    parser.add_argument(
        "--yolo-confidence",
        type=float,
        help="Override the YOLO confidence threshold from the config.",
    )
    parser.add_argument(
        "--yolo-labels",
        help="Comma-separated YOLO labels to allow at runtime.",
    )
    parser.add_argument(
        "--frame-image",
        help="Optional image or .npy frame file to use instead of live screen capture.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        help="Override the loop interval from the config.",
    )
    parser.add_argument(
        "--max-loops",
        type=int,
        help="Override the max loop count from the config. Use 0 for infinite.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run mode for safe macro testing.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Force live input mode and send real mouse or keyboard events.",
    )
    parser.add_argument(
        "--print-config-summary",
        action="store_true",
        help="Print the resolved config summary and exit.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.dry_run and args.live:
        raise SystemExit("Choose either --dry-run or --live, not both.")

    if args.write_sample_config:
        path = write_sample_config(Path(args.config))
        print(f"wrote sample config to {path}")
        return

    if args.print_config_summary:
        config = AppConfig.load(args.config)
        summary = {
            "capture_region": config.capture_region.as_tuple(),
            "runtime": {
                "interval_seconds": config.runtime.interval_seconds,
                "dry_run": config.runtime.dry_run,
                "max_loops": config.runtime.max_loops,
            },
            "detector_backend": config.detector.backend,
            "template_count": len(config.templates),
            "yolo_target_count": len(config.yolo.targets),
            "frame_image": args.frame_image,
        }
        print(json.dumps(summary, indent=2))
        return

    if args.mode == "web":
        from winvision_macro.web_control import run_web_control

        run_web_control(
            host=args.host,
            port=args.port,
            default_config_path=args.config,
        )
        return

    yolo_labels = [item.strip() for item in args.yolo_labels.split(",")] if args.yolo_labels else None
    dry_run_override = True if args.dry_run else False if args.live else None
    config, runner, controller = build_runtime_stack(
        config_path=args.config,
        dry_run=dry_run_override,
        interval_seconds=args.interval_seconds,
        max_loops=args.max_loops,
        detector_backend=args.detector_backend,
        yolo_model_path=args.yolo_model_path,
        yolo_confidence_threshold=args.yolo_confidence,
        yolo_labels=yolo_labels,
        frame_image_path=args.frame_image,
    )

    if args.once:
        detections = runner.run_once()
        if detections:
            for item in detections:
                center_x, center_y = item.box.center
                print(
                    f"name={item.name} score={item.score:.3f} "
                    f"center=({center_x},{center_y}) action={item.action.type}"
                )
        else:
            print("no detections")
        print("actions:", ", ".join(controller.action_log) if controller.action_log else "(none)")
        return

    max_loops = config.runtime.max_loops
    print(
        "starting runtime:",
        f"backend={config.detector.backend}",
        f"interval={config.runtime.interval_seconds}",
        f"dry_run={config.runtime.dry_run}",
        f"max_loops={max_loops or 'infinite'}",
    )

    def on_loop(loop_index: int, detections) -> None:
        top = detections[0] if detections else None
        if top is None:
            print(f"loop={loop_index:03d} no detections")
            return
        center_x, center_y = top.box.center
        print(
            f"loop={loop_index:03d} top={top.name} score={top.score:.3f} "
            f"center=({center_x},{center_y}) action={top.action.type}"
        )

    try:
        runner.run(max_loops=max_loops, on_loop=on_loop)
    except KeyboardInterrupt:
        print("\nstopped by user")

    print("actions:", ", ".join(controller.action_log) if controller.action_log else "(none)")
