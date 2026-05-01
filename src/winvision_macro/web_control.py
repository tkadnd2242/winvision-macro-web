from __future__ import annotations

import html
import json
import queue
import threading
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from winvision_macro.bootstrap import build_runtime_stack
from winvision_macro.config import write_sample_config


def _render_page(default_config_path: str) -> str:
    config_value = html.escape(default_config_path, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WinVision Macro Control</title>
  <style>
    :root {{
      --bg: #111318;
      --panel: rgba(20, 24, 31, 0.9);
      --panel-strong: rgba(30, 36, 46, 0.95);
      --line: #2a3241;
      --ink: #eef2f7;
      --muted: #9aa7ba;
      --accent: #59c7a7;
      --accent-strong: #3fb895;
      --warn: #e8b04d;
      --danger: #e06b6b;
      --shadow: rgba(0, 0, 0, 0.35);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: "Bahnschrift", "Segoe UI Variable", "Trebuchet MS", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(89, 199, 167, 0.18), transparent 34%),
        radial-gradient(circle at top right, rgba(88, 122, 255, 0.16), transparent 28%),
        linear-gradient(160deg, #0d1015 0%, #171c24 55%, #0f1318 100%);
    }}
    .page {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px 18px 36px;
    }}
    .hero {{
      padding: 28px;
      border: 1px solid var(--line);
      border-radius: 24px;
      background: linear-gradient(180deg, rgba(21, 26, 34, 0.92), rgba(15, 19, 25, 0.92));
      box-shadow: 0 18px 60px var(--shadow);
      position: relative;
      overflow: hidden;
    }}
    .hero::after {{
      content: "";
      position: absolute;
      inset: auto -80px -110px auto;
      width: 240px;
      height: 240px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(89, 199, 167, 0.22), transparent 65%);
      pointer-events: none;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(30px, 5vw, 46px);
      line-height: 1;
      letter-spacing: 0.02em;
      text-transform: uppercase;
    }}
    .hero p {{
      margin: 0;
      max-width: 780px;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.65;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 18px;
      margin-top: 18px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 20px;
      box-shadow: 0 14px 40px var(--shadow);
      backdrop-filter: blur(14px);
    }}
    .card h2 {{
      margin: 0 0 14px;
      font-size: 18px;
      letter-spacing: 0.03em;
      text-transform: uppercase;
    }}
    .form-grid {{
      display: grid;
      grid-template-columns: 150px 1fr;
      gap: 12px 14px;
      align-items: center;
    }}
    .wide {{
      grid-column: 1 / -1;
    }}
    label {{
      color: var(--muted);
      font-size: 14px;
      letter-spacing: 0.03em;
      text-transform: uppercase;
    }}
    input[type="text"], input[type="number"], select {{
      width: 100%;
      border: 1px solid #314056;
      border-radius: 14px;
      padding: 12px 14px;
      background: rgba(12, 16, 22, 0.88);
      color: var(--ink);
      font-size: 15px;
      outline: none;
    }}
    input[type="text"]:focus, input[type="number"]:focus, select:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(89, 199, 167, 0.12);
    }}
    .toggle {{
      display: inline-flex;
      gap: 10px;
      align-items: center;
      color: var(--ink);
      font-size: 15px;
    }}
    .toggle input {{
      width: 18px;
      height: 18px;
      accent-color: var(--accent);
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}
    button {{
      border: 0;
      border-radius: 999px;
      padding: 12px 16px;
      font-size: 14px;
      font-family: inherit;
      font-weight: 700;
      letter-spacing: 0.03em;
      cursor: pointer;
      color: #06110d;
      background: var(--accent);
      transition: transform 120ms ease, background 120ms ease;
    }}
    button:hover {{
      transform: translateY(-1px);
      background: var(--accent-strong);
    }}
    button.secondary {{
      background: #89a9ff;
      color: #081120;
    }}
    button.secondary:hover {{
      background: #7598f4;
    }}
    button.warn {{
      background: var(--warn);
      color: #171004;
    }}
    button.warn:hover {{
      background: #db9d31;
    }}
    button.danger {{
      background: var(--danger);
      color: white;
    }}
    button.danger:hover {{
      background: #d45757;
    }}
    .status {{
      margin-top: 16px;
      padding: 14px 16px;
      border-radius: 16px;
      background: var(--panel-strong);
      border: 1px solid var(--line);
      font-family: "Consolas", "SFMono-Regular", monospace;
      color: var(--muted);
    }}
    .tips {{
      display: grid;
      gap: 12px;
    }}
    .tip {{
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(21, 27, 35, 0.92), rgba(17, 22, 28, 0.92));
    }}
    .tip strong {{
      display: block;
      margin-bottom: 6px;
      font-size: 13px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: var(--accent);
    }}
    .tip span {{
      color: var(--muted);
      line-height: 1.6;
      font-size: 14px;
    }}
    .console {{
      margin-top: 18px;
      padding: 18px;
      min-height: 420px;
      border-radius: 22px;
      border: 1px solid var(--line);
      background:
        linear-gradient(180deg, rgba(7, 10, 14, 0.96), rgba(14, 18, 24, 0.96));
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
      font-family: "Consolas", "SFMono-Regular", monospace;
      font-size: 13px;
      line-height: 1.55;
      white-space: pre-wrap;
      overflow: auto;
    }}
    .footer {{
      margin-top: 14px;
      color: var(--muted);
      font-size: 13px;
    }}
    .preview-card {{
      margin-top: 18px;
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 18px;
      align-items: start;
    }}
    .preview-frame {{
      border-radius: 22px;
      overflow: hidden;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(10, 14, 18, 0.96), rgba(19, 24, 30, 0.96));
      min-height: 340px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }}
    .preview-frame img {{
      width: 100%;
      display: block;
      object-fit: contain;
    }}
    .preview-empty {{
      padding: 30px;
      color: var(--muted);
      text-align: center;
      line-height: 1.7;
    }}
    .preview-actions {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }}
    .meta-list {{
      display: grid;
      gap: 10px;
    }}
    .meta-item {{
      padding: 12px 14px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(21, 27, 35, 0.92), rgba(16, 21, 28, 0.92));
    }}
    .meta-item strong {{
      display: block;
      margin-bottom: 4px;
      color: var(--ink);
      font-size: 14px;
    }}
    .meta-item span {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
    }}
    @media (max-width: 900px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}
      .form-grid {{
        grid-template-columns: 1fr;
      }}
      .preview-card {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <h1>WinVision Macro</h1>
      <p>
        OpenCV template detection and <code>pyautogui</code> input control through a local browser dashboard.
        Start with dry-run enabled, confirm detections in the console, then switch to real input only after calibration.
      </p>
    </section>

    <section class="layout">
      <div class="card">
        <h2>Control Deck</h2>
        <div class="form-grid">
          <label for="config_path">Config Path</label>
          <input id="config_path" type="text" value="{config_value}">

          <label for="detector_backend">Detector</label>
          <select id="detector_backend">
            <option value="template">Template Match</option>
            <option value="yolo">YOLO</option>
          </select>

          <label for="interval_seconds">Interval</label>
          <input id="interval_seconds" type="number" min="0.05" step="0.05" value="0.35">

          <label for="max_loops">Max Loops</label>
          <input id="max_loops" type="number" min="0" step="1" value="200">

          <label for="yolo_model_path">YOLO Model</label>
          <input id="yolo_model_path" type="text" value="models/best.pt">

          <label for="yolo_confidence">YOLO Confidence</label>
          <input id="yolo_confidence" type="number" min="0" max="1" step="0.01" value="0.50">

          <label for="yolo_labels">YOLO Labels</label>
          <input id="yolo_labels" type="text" value="" placeholder="enemy, confirm, skill_ready">

          <label class="wide toggle">
            <input id="dry_run" type="checkbox" checked>
            <span>Dry run only</span>
          </label>
        </div>

        <div class="actions">
          <button onclick="postAction('/api/write-config')">Write Sample Config</button>
          <button class="secondary" onclick="postAction('/api/run-once')">Run Once</button>
          <button class="warn" onclick="postAction('/api/start')">Start Loop</button>
          <button class="danger" onclick="postAction('/api/stop')">Stop</button>
        </div>

        <div id="status" class="status">Ready</div>
      </div>

      <div class="card">
        <h2>Workflow</h2>
        <div class="tips">
          <div class="tip">
            <strong>Step 1</strong>
            <span>Generate the sample JSON and update the screen region plus template file paths for your Windows desktop layout.</span>
          </div>
          <div class="tip">
            <strong>Step 2</strong>
            <span>Keep dry-run enabled while checking whether the top detection name and score match what is really on screen.</span>
          </div>
          <div class="tip">
            <strong>Step 3</strong>
            <span>Once detections are stable, disable dry-run and run the live loop from this browser panel.</span>
          </div>
        </div>
      </div>
    </section>

    <section class="preview-card">
      <div class="card">
        <h2>Live Preview</h2>
        <div class="preview-actions">
          <button class="secondary" onclick="refreshPreview()">Refresh Preview</button>
          <label class="toggle">
            <input id="auto_preview" type="checkbox" checked>
            <span>Auto refresh</span>
          </label>
        </div>
        <div class="preview-frame">
          <img id="preview_image" alt="preview" style="display:none;">
          <div id="preview_empty" class="preview-empty">
            No preview yet.<br>
            Capture a frame from the browser and confirm the detection boxes here.
          </div>
        </div>
      </div>

      <div class="card">
        <h2>Detection Feed</h2>
        <div id="preview_summary" class="status">Preview idle</div>
        <div id="preview_meta" class="meta-list" style="margin-top:14px;"></div>
      </div>
    </section>

    <section class="console" id="console">dashboard ready\n</section>
    <div class="footer">Local-only dashboard. Keep your game window and templates aligned to the same Windows resolution and scaling.</div>
  </div>

  <script>
    let previewBusy = false;

    async function postAction(path) {{
      const payload = {{
        config_path: document.getElementById('config_path').value,
        detector_backend: document.getElementById('detector_backend').value,
        interval_seconds: Number(document.getElementById('interval_seconds').value || 0.35),
        max_loops: Number(document.getElementById('max_loops').value || 0),
        dry_run: document.getElementById('dry_run').checked,
        yolo_model_path: document.getElementById('yolo_model_path').value,
        yolo_confidence: Number(document.getElementById('yolo_confidence').value || 0.5),
        yolo_labels: document.getElementById('yolo_labels').value
      }};

      const response = await fetch(path, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload)
      }});
      const data = await response.json();
      document.getElementById('status').textContent = data.status || 'Ready';
      if (data.error) {{
        appendLine('[error] ' + data.error);
      }}
    }}

    function appendLine(line) {{
      const consoleEl = document.getElementById('console');
      consoleEl.textContent += line + "\\n";
      consoleEl.scrollTop = consoleEl.scrollHeight;
    }}

    function renderPreviewMeta(detections) {{
      const meta = document.getElementById('preview_meta');
      meta.innerHTML = '';
      if (!detections || detections.length === 0) {{
        meta.innerHTML = '<div class="meta-item"><strong>No detections</strong><span>Nothing matched the configured templates in this frame.</span></div>';
        return;
      }}

      for (const item of detections) {{
        const box = document.createElement('div');
        box.className = 'meta-item';
        box.innerHTML =
          '<strong>' + item.name + ' (' + item.score.toFixed(3) + ')' + '</strong>' +
          '<span>center=(' + item.center[0] + ',' + item.center[1] + ') action=' + item.action + '</span>';
        meta.appendChild(box);
      }}
    }}

    function renderPreviewError(message) {{
      document.getElementById('preview_summary').textContent = message;
      document.getElementById('preview_meta').innerHTML =
        '<div class="meta-item"><strong>Preview Error</strong><span>' + message + '</span></div>';
    }}

    async function refreshPreview() {{
      if (previewBusy) {{
        return;
      }}
      previewBusy = true;
      try {{
        const payload = {{
          config_path: document.getElementById('config_path').value,
          detector_backend: document.getElementById('detector_backend').value,
          interval_seconds: Number(document.getElementById('interval_seconds').value || 0.35),
          max_loops: Number(document.getElementById('max_loops').value || 0),
          dry_run: document.getElementById('dry_run').checked,
          yolo_model_path: document.getElementById('yolo_model_path').value,
          yolo_confidence: Number(document.getElementById('yolo_confidence').value || 0.5),
          yolo_labels: document.getElementById('yolo_labels').value
        }};

        const response = await fetch('/api/preview', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload)
        }});
        const data = await response.json();
        if (data.error) {{
          renderPreviewError(data.error);
          return;
        }}

        const image = document.getElementById('preview_image');
        const empty = document.getElementById('preview_empty');
        image.src = data.image_data;
        image.style.display = 'block';
        empty.style.display = 'none';

        document.getElementById('preview_summary').textContent =
          'backend=' + (data.detector_backend || 'template') + ' ' +
          'detections=' + data.detection_count +
          ' image=' + data.image_width + 'x' + data.image_height;
        renderPreviewMeta(data.detections || []);
      }} catch (error) {{
        renderPreviewError('failed to refresh preview');
      }} finally {{
        previewBusy = false;
      }}
    }}

    async function pollState() {{
      try {{
        const response = await fetch('/api/state');
        const data = await response.json();
        document.getElementById('status').textContent = data.status || 'Ready';
        for (const line of data.lines || []) {{
          appendLine(line);
        }}
      }} catch (error) {{
        appendLine('[error] failed to fetch state');
      }}
      window.setTimeout(pollState, 900);
    }}

    async function previewLoop() {{
      if (document.getElementById('auto_preview').checked) {{
        await refreshPreview();
      }}
      window.setTimeout(previewLoop, 1800);
    }}

    pollState();
    previewLoop();
  </script>
</body>
</html>"""


@dataclass
class WebControlState:
    log_queue: queue.Queue[str]
    status: str = "Ready"
    worker_thread: threading.Thread | None = None
    stop_event: threading.Event = field(default_factory=threading.Event)

    def log(self, line: str) -> None:
        self.log_queue.put(line)

    def set_status(self, value: str) -> None:
        self.status = value

    def take_logs(self) -> list[str]:
        lines: list[str] = []
        while True:
            try:
                lines.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        return lines

    def start_task(self, label: str, task: Callable[[], None]) -> tuple[bool, str | None]:
        if self.worker_thread is not None and self.worker_thread.is_alive():
            return False, "Another task is already running."

        self.stop_event.clear()
        self.set_status(f"Running {label}...")

        def wrapped() -> None:
            try:
                task()
                self.log(f"[done] {label}")
                self.set_status("Ready")
            except Exception as exc:
                self.log(f"[error] {exc}")
                self.set_status("Error")

        self.worker_thread = threading.Thread(target=wrapped, daemon=True)
        self.worker_thread.start()
        return True, None

    def stop(self) -> None:
        self.stop_event.set()
        self.set_status("Stopping after current loop...")
        self.log("[info] stop requested")


class WebControlService:
    def __init__(self, default_config_path: str) -> None:
        self.default_config_path = default_config_path
        self.state = WebControlState(log_queue=queue.Queue())

    def write_sample(self, config_path: str) -> None:
        path = write_sample_config(Path(config_path))
        self.state.log(f"[write] sample config created at {path}")

    def preview(
        self,
        config_path: str,
        dry_run: bool,
        interval_seconds: float,
        max_loops: int,
        detector_backend: str | None,
        yolo_model_path: str | None,
        yolo_confidence: float | None,
        yolo_labels: list[str] | None,
    ) -> dict[str, object]:
        from winvision_macro.preview import build_preview_payload

        config, runner, _controller = build_runtime_stack(
            config_path=config_path,
            dry_run=dry_run,
            interval_seconds=interval_seconds,
            max_loops=max_loops,
            detector_backend=detector_backend,
            yolo_model_path=yolo_model_path,
            yolo_confidence_threshold=yolo_confidence,
            yolo_labels=yolo_labels,
        )
        frame = runner.frame_source.capture()
        detections = runner.detector.detect(frame)
        payload = build_preview_payload(frame, detections, config.capture_region)
        payload["detector_backend"] = config.detector.backend
        return payload

    def run_once(
        self,
        config_path: str,
        dry_run: bool,
        interval_seconds: float,
        max_loops: int,
        detector_backend: str | None,
        yolo_model_path: str | None,
        yolo_confidence: float | None,
        yolo_labels: list[str] | None,
    ) -> None:
        config, runner, controller = build_runtime_stack(
            config_path=config_path,
            dry_run=dry_run,
            interval_seconds=interval_seconds,
            max_loops=max_loops,
            detector_backend=detector_backend,
            yolo_model_path=yolo_model_path,
            yolo_confidence_threshold=yolo_confidence,
            yolo_labels=yolo_labels,
        )
        self.state.log(f"[backend] {config.detector.backend}")
        detections = runner.run_once()
        if detections:
            self.state.log(f"[detect] {len(detections)} detections found")
            for item in detections[:5]:
                center_x, center_y = item.box.center
                self.state.log(
                    f"[match] name={item.name} score={item.score:.3f} "
                    f"center=({center_x},{center_y}) action={item.action.type}"
                )
        else:
            self.state.log("[detect] no detections")

        if controller.action_log:
            self.state.log("[action] " + ", ".join(controller.action_log))
        else:
            self.state.log("[action] none")

    def start_loop(
        self,
        config_path: str,
        dry_run: bool,
        interval_seconds: float,
        max_loops: int,
        detector_backend: str | None,
        yolo_model_path: str | None,
        yolo_confidence: float | None,
        yolo_labels: list[str] | None,
    ) -> None:
        config, runner, controller = build_runtime_stack(
            config_path=config_path,
            dry_run=dry_run,
            interval_seconds=interval_seconds,
            max_loops=max_loops,
            detector_backend=detector_backend,
            yolo_model_path=yolo_model_path,
            yolo_confidence_threshold=yolo_confidence,
            yolo_labels=yolo_labels,
        )
        self.state.log(
            f"[start] backend={config.detector.backend} "
            f"interval={config.runtime.interval_seconds} "
            f"dry_run={config.runtime.dry_run} "
            f"max_loops={config.runtime.max_loops or 'infinite'}"
        )
        action_count = 0

        def on_loop(loop_index, detections) -> None:
            nonlocal action_count
            top = detections[0] if detections else None
            if top is None:
                self.state.log(f"[loop {loop_index:03d}] no detections")
            else:
                center_x, center_y = top.box.center
                self.state.log(
                    f"[loop {loop_index:03d}] top={top.name} score={top.score:.3f} "
                    f"center=({center_x},{center_y}) action={top.action.type}"
                )
            if len(controller.action_log) > action_count:
                for line in controller.action_log[action_count:]:
                    self.state.log(f"[loop {loop_index:03d}] action={line}")
                action_count = len(controller.action_log)

        runner.run(
            max_loops=config.runtime.max_loops,
            on_loop=on_loop,
            should_stop=self.state.stop_event.is_set,
        )
        self.state.log("[stop] loop finished")


def _parse_payload(raw: bytes) -> dict[str, object]:
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _as_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv_labels(value: object) -> list[str] | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return [item.strip() for item in text.split(",") if item.strip()]


def make_handler(service: WebControlService):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_html(_render_page(service.default_config_path))
                return
            if parsed.path == "/api/state":
                self._send_json(
                    {
                        "status": service.state.status,
                        "lines": service.state.take_logs(),
                    }
                )
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = _parse_payload(self.rfile.read(length))
            config_path = str(payload.get("config_path", service.default_config_path))
            interval_seconds = float(payload.get("interval_seconds", 0.35) or 0.35)
            max_loops = int(payload.get("max_loops", 0) or 0)
            dry_run = _as_bool(payload.get("dry_run"), True)
            detector_backend = str(payload.get("detector_backend", "")).strip() or None
            yolo_model_path = str(payload.get("yolo_model_path", "")).strip() or None
            yolo_confidence_raw = payload.get("yolo_confidence")
            yolo_confidence = float(yolo_confidence_raw) if yolo_confidence_raw not in (None, "") else None
            yolo_labels = _parse_csv_labels(payload.get("yolo_labels"))

            if self.path == "/api/write-config":
                service.write_sample(config_path)
                self._send_json({"status": service.state.status or "Ready"})
                return

            if self.path == "/api/preview":
                try:
                    preview = service.preview(
                        config_path,
                        dry_run,
                        interval_seconds,
                        max_loops,
                        detector_backend,
                        yolo_model_path,
                        yolo_confidence,
                        yolo_labels,
                    )
                except Exception as exc:
                    self._send_json({"status": service.state.status, "error": str(exc)})
                    return
                preview["status"] = service.state.status
                self._send_json(preview)
                return

            if self.path == "/api/stop":
                service.state.stop()
                self._send_json({"status": service.state.status})
                return

            task_map = {
                "/api/run-once": (
                    "single pass",
                    lambda: service.run_once(
                        config_path,
                        dry_run,
                        interval_seconds,
                        max_loops,
                        detector_backend,
                        yolo_model_path,
                        yolo_confidence,
                        yolo_labels,
                    ),
                ),
                "/api/start": (
                    "runtime loop",
                    lambda: service.start_loop(
                        config_path,
                        dry_run,
                        interval_seconds,
                        max_loops,
                        detector_backend,
                        yolo_model_path,
                        yolo_confidence,
                        yolo_labels,
                    ),
                ),
            }
            task_entry = task_map.get(self.path)
            if task_entry is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return

            label, task = task_entry
            ok, error = service.state.start_task(label, task)
            if not ok:
                self._send_json(
                    {"status": service.state.status, "error": error},
                    status=HTTPStatus.CONFLICT,
                )
                return

            self._send_json({"status": service.state.status})

        def log_message(self, format: str, *args) -> None:
            return

        def _send_html(self, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(self, data: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return Handler


def run_web_control(
    host: str = "127.0.0.1",
    port: int = 8765,
    default_config_path: str = "configs/default.json",
) -> None:
    service = WebControlService(default_config_path=default_config_path)
    server = ThreadingHTTPServer((host, port), make_handler(service))
    print(f"web control running at http://{host}:{port}")
    print("stop with Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped by user")
    finally:
        server.server_close()
