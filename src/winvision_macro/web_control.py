from __future__ import annotations

import html
import json
import queue
import threading
import time
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from winvision_macro.bootstrap import build_runtime_stack
from winvision_macro.config import AppConfig, write_sample_config


_LIVE_ARM_PHRASE = "ARM LIVE INPUT"
_LIVE_ARM_MINUTES = 10.0


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
    .calibration-layout {{
      margin-top: 18px;
      display: grid;
      grid-template-columns: 1.12fr 0.88fr;
      gap: 18px;
      align-items: start;
    }}
    .selection-surface {{
      position: relative;
      margin-top: 16px;
      border-radius: 22px;
      overflow: hidden;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(10, 14, 18, 0.96), rgba(19, 24, 30, 0.96));
      min-height: 320px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: crosshair;
    }}
    .selection-surface img {{
      width: 100%;
      display: block;
    }}
    .selection-box {{
      position: absolute;
      border: 2px solid #59c7a7;
      background: rgba(89, 199, 167, 0.18);
      box-shadow: 0 0 0 1px rgba(255,255,255,0.12) inset;
      pointer-events: none;
    }}
    .calibration-grid {{
      margin-top: 14px;
    }}
    .calibration-grid input[readonly] {{
      opacity: 0.95;
    }}
    .note {{
      margin-top: 12px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }}
    .summary-card {{
      margin-top: 18px;
      display: grid;
      grid-template-columns: 0.9fr 1.1fr;
      gap: 18px;
      align-items: start;
    }}
    .summary-list {{
      display: grid;
      gap: 10px;
      margin-top: 14px;
    }}
    .summary-item {{
      padding: 12px 14px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(21, 27, 35, 0.92), rgba(16, 21, 28, 0.92));
    }}
    .summary-item strong {{
      display: block;
      margin-bottom: 4px;
      color: var(--ink);
      font-size: 14px;
    }}
    .summary-item span {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }}
    .safety-pill {{
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(15, 19, 25, 0.9);
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }}
    .safety-pill.armed {{
      color: #09120c;
      border-color: rgba(89, 199, 167, 0.6);
      background: var(--accent);
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
      .calibration-layout {{
        grid-template-columns: 1fr;
      }}
      .summary-card {{
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

          <label for="frame_image_path">Frame Image</label>
          <input id="frame_image_path" type="text" value="" placeholder="optional: captures/sample_screen.png or sample_frame.npy">

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
            <span>Generate the sample JSON, capture the desktop in Calibration Studio, and drag a region around your game window.</span>
          </div>
          <div class="tip">
            <strong>Step 2</strong>
            <span>Save cropped UI elements straight into <code>templates/</code>, then keep dry-run enabled while checking the preview detections or a saved test frame.</span>
          </div>
          <div class="tip">
            <strong>Step 3</strong>
            <span>Once detections are stable, disable dry-run and run the live loop from this browser panel.</span>
          </div>
        </div>
      </div>
    </section>

    <section class="summary-card">
      <div class="card">
        <h2>Safety Lock</h2>
        <div class="preview-actions">
          <span id="live_status_badge" class="safety-pill">Locked</span>
        </div>
        <div class="form-grid">
          <label for="live_arm_phrase">Arm Phrase</label>
          <input id="live_arm_phrase" type="text" value="" placeholder="ARM LIVE INPUT">
        </div>
        <div class="actions">
          <button class="warn" onclick="armLiveInput()">Arm Live Input</button>
          <button class="danger" onclick="disarmLiveInput()">Disarm</button>
        </div>
        <div id="live_status_text" class="status">Dry-run is safe by default. Live input stays locked until you arm it explicitly.</div>
      </div>

      <div class="card">
        <h2>Config Snapshot</h2>
        <div class="preview-actions">
          <button class="secondary" onclick="refreshConfigSummary()">Refresh Config</button>
        </div>
        <div id="config_summary_status" class="status">Config summary idle</div>
        <div id="config_summary_templates" class="summary-list"></div>
        <div id="config_summary_yolo" class="summary-list" style="margin-top:14px;"></div>
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

    <section class="calibration-layout">
      <div class="card">
        <h2>Calibration Studio</h2>
        <div class="preview-actions">
          <button onclick="captureCalibration()">Capture Desktop</button>
          <button class="secondary" onclick="applyCalibrationRegion()">Apply Region To Config</button>
        </div>
        <div class="form-grid calibration-grid">
          <label for="selection_left">Left</label>
          <input id="selection_left" type="number" min="0" step="1" value="0">

          <label for="selection_top">Top</label>
          <input id="selection_top" type="number" min="0" step="1" value="0">

          <label for="selection_width">Width</label>
          <input id="selection_width" type="number" min="1" step="1" value="0">

          <label for="selection_height">Height</label>
          <input id="selection_height" type="number" min="1" step="1" value="0">
        </div>
        <div id="calibration_status" class="status">Capture the desktop, then drag across the image to pick a region.</div>
        <div class="selection-surface" id="selection_surface">
          <img id="calibration_image" alt="desktop calibration" style="display:none;">
          <div id="selection_box" class="selection-box" style="display:none;"></div>
          <div id="calibration_empty" class="preview-empty">
            No desktop capture yet.<br>
            Grab one frame, draw a selection, and use it as the capture region or a template crop.
          </div>
        </div>
      </div>

      <div class="card">
        <h2>Template Crop</h2>
        <div class="form-grid">
          <label for="template_name">Template Name</label>
          <input id="template_name" type="text" value="" placeholder="target_button">

          <label for="template_path">Template Path</label>
          <input id="template_path" type="text" value="" placeholder="templates/target_button.png">

          <label for="template_threshold">Threshold</label>
          <input id="template_threshold" type="number" min="0" max="1" step="0.01" value="0.92">

          <label for="template_cooldown">Cooldown</label>
          <input id="template_cooldown" type="number" min="0" step="0.05" value="0.75">

          <label for="template_action_type">Action</label>
          <select id="template_action_type">
            <option value="click_center">click_center</option>
            <option value="double_click_center">double_click_center</option>
            <option value="press_key">press_key</option>
          </select>

          <label for="template_action_key">Action Key</label>
          <input id="template_action_key" type="text" value="" placeholder="1">

          <label class="wide toggle">
            <input id="template_add_to_config" type="checkbox" checked>
            <span>Save template metadata into the config file</span>
          </label>
        </div>
        <div class="actions">
          <button class="warn" onclick="saveTemplateCrop()">Save Template Crop</button>
        </div>
        <div id="template_status" class="status">Select a region from the captured desktop first.</div>
        <div class="note">
          The crop is saved from the full desktop capture, so you can pick either the whole game window or a small UI element from the same screenshot.
        </div>
      </div>
    </section>

    <section class="console" id="console">dashboard ready\n</section>
    <div class="footer">Local-only dashboard. Keep your game window and templates aligned to the same Windows resolution and scaling.</div>
  </div>

  <script>
    let previewBusy = false;
    let calibrationBusy = false;
    let calibrationSourceSize = null;
    let dragState = null;

    function buildBasePayload() {{
      return {{
        config_path: document.getElementById('config_path').value,
        detector_backend: document.getElementById('detector_backend').value,
        interval_seconds: Number(document.getElementById('interval_seconds').value || 0.35),
        max_loops: Number(document.getElementById('max_loops').value || 0),
        dry_run: document.getElementById('dry_run').checked,
        yolo_model_path: document.getElementById('yolo_model_path').value,
        yolo_confidence: Number(document.getElementById('yolo_confidence').value || 0.5),
        yolo_labels: document.getElementById('yolo_labels').value,
        frame_image_path: document.getElementById('frame_image_path').value
      }};
    }}

    async function postAction(path) {{
      const response = await fetch(path, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(buildBasePayload())
      }});
      const data = await response.json();
      document.getElementById('status').textContent = data.status || 'Ready';
      if (typeof data.live_input_armed !== 'undefined') {{
        updateLiveSafety(data);
      }}
      if (data.error) {{
        appendLine('[error] ' + data.error);
        return;
      }}
      if (path === '/api/write-config') {{
        refreshConfigSummary();
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

    function updateLiveSafety(data) {{
      const badge = document.getElementById('live_status_badge');
      const text = document.getElementById('live_status_text');
      const armed = Boolean(data.live_input_armed);
      const secondsLeft = Number(data.live_input_seconds_left || 0);
      badge.textContent = armed ? 'Armed' : 'Locked';
      badge.className = armed ? 'safety-pill armed' : 'safety-pill';
      if (armed) {{
        text.textContent = 'Live input armed for about ' + Math.ceil(secondsLeft) + ' more seconds.';
      }} else {{
        text.textContent = 'Dry-run is safe by default. Live input stays locked until you arm it explicitly.';
      }}
    }}

    function renderConfigList(rootId, heading, items, formatter) {{
      const root = document.getElementById(rootId);
      if (!items || items.length === 0) {{
        root.innerHTML = '<div class="summary-item"><strong>' + heading + '</strong><span>None configured.</span></div>';
        return;
      }}
      root.innerHTML = items.map((item) => {{
        const entry = formatter(item);
        return '<div class="summary-item"><strong>' + entry.title + '</strong><span>' + entry.body + '</span></div>';
      }}).join('');
    }}

    async function refreshConfigSummary() {{
      const response = await fetch('/api/config-summary', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(buildBasePayload())
      }});
      const data = await response.json();
      if (data.error) {{
        document.getElementById('config_summary_status').textContent = data.error;
        return;
      }}
      updateLiveSafety(data);
      document.getElementById('config_summary_status').textContent =
        'region=(' + data.capture_region.left + ',' + data.capture_region.top + ',' +
        data.capture_region.width + 'x' + data.capture_region.height + ') ' +
        'templates=' + data.template_count + ' yolo_targets=' + data.yolo_target_count;

      renderConfigList('config_summary_templates', 'Templates', data.templates || [], (item) => {{
        return {{
          title: item.name + ' [' + item.primary_action + ']',
          body: 'path=' + item.path +
            ' threshold=' + Number(item.threshold).toFixed(2) +
            ' cooldown=' + Number(item.cooldown_seconds).toFixed(2) +
            ' priority=' + item.priority +
            ' steps=' + item.action_count
        }};
      }});

      renderConfigList('config_summary_yolo', 'YOLO Targets', data.yolo_targets || [], (item) => {{
        return {{
          title: item.label + ' [' + item.primary_action + ']',
          body: 'min_conf=' + Number(item.min_confidence).toFixed(2) +
            ' cooldown=' + Number(item.cooldown_seconds).toFixed(2) +
            ' priority=' + item.priority +
            ' steps=' + item.action_count
        }};
      }});
    }}

    async function armLiveInput() {{
      const payload = buildBasePayload();
      payload.live_arm_phrase = document.getElementById('live_arm_phrase').value;
      const response = await fetch('/api/live/arm', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload)
      }});
      const data = await response.json();
      if (data.error) {{
        appendLine('[error] ' + data.error);
        document.getElementById('live_status_text').textContent = data.error;
        return;
      }}
      updateLiveSafety(data);
      document.getElementById('live_arm_phrase').value = '';
    }}

    async function disarmLiveInput() {{
      const response = await fetch('/api/live/disarm', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(buildBasePayload())
      }});
      const data = await response.json();
      updateLiveSafety(data);
    }}

    function getSelection() {{
      return {{
        left: Number(document.getElementById('selection_left').value || 0),
        top: Number(document.getElementById('selection_top').value || 0),
        width: Number(document.getElementById('selection_width').value || 0),
        height: Number(document.getElementById('selection_height').value || 0)
      }};
    }}

    function hasSelection(selection) {{
      return selection.width > 0 && selection.height > 0;
    }}

    function describeSelection(selection) {{
      return 'left=' + selection.left +
        ' top=' + selection.top +
        ' width=' + selection.width +
        ' height=' + selection.height;
    }}

    function writeSelection(selection) {{
      document.getElementById('selection_left').value = Math.max(0, Math.round(selection.left || 0));
      document.getElementById('selection_top').value = Math.max(0, Math.round(selection.top || 0));
      document.getElementById('selection_width').value = Math.max(0, Math.round(selection.width || 0));
      document.getElementById('selection_height').value = Math.max(0, Math.round(selection.height || 0));
      renderSelectionBox();
      if (hasSelection(getSelection())) {{
        document.getElementById('calibration_status').textContent = 'Selected ' + describeSelection(getSelection());
      }}
    }}

    function renderSelectionBox() {{
      const image = document.getElementById('calibration_image');
      const box = document.getElementById('selection_box');
      const selection = getSelection();
      if (!calibrationSourceSize || image.style.display === 'none' || !hasSelection(selection)) {{
        box.style.display = 'none';
        return;
      }}

      const rect = image.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) {{
        box.style.display = 'none';
        return;
      }}

      box.style.display = 'block';
      box.style.left = (selection.left * rect.width / calibrationSourceSize.width) + 'px';
      box.style.top = (selection.top * rect.height / calibrationSourceSize.height) + 'px';
      box.style.width = (selection.width * rect.width / calibrationSourceSize.width) + 'px';
      box.style.height = (selection.height * rect.height / calibrationSourceSize.height) + 'px';
    }}

    function getCalibrationPoint(clientX, clientY) {{
      if (!calibrationSourceSize) {{
        return null;
      }}
      const image = document.getElementById('calibration_image');
      if (image.style.display === 'none') {{
        return null;
      }}
      const rect = image.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) {{
        return null;
      }}
      const clampedX = Math.max(rect.left, Math.min(clientX, rect.right));
      const clampedY = Math.max(rect.top, Math.min(clientY, rect.bottom));
      return {{
        x: Math.round((clampedX - rect.left) * calibrationSourceSize.width / rect.width),
        y: Math.round((clampedY - rect.top) * calibrationSourceSize.height / rect.height)
      }};
    }}

    function buildSelectionFromPoints(start, end) {{
      const left = Math.min(start.x, end.x);
      const top = Math.min(start.y, end.y);
      const width = Math.max(1, Math.abs(end.x - start.x));
      const height = Math.max(1, Math.abs(end.y - start.y));
      return {{ left, top, width, height }};
    }}

    function setupCalibrationSelection() {{
      const surface = document.getElementById('selection_surface');
      const image = document.getElementById('calibration_image');
      const fields = ['selection_left', 'selection_top', 'selection_width', 'selection_height'];

      surface.addEventListener('mousedown', (event) => {{
        const point = getCalibrationPoint(event.clientX, event.clientY);
        if (!point) {{
          return;
        }}
        dragState = {{ start: point }};
        writeSelection({{ left: point.x, top: point.y, width: 1, height: 1 }});
        event.preventDefault();
      }});

      window.addEventListener('mousemove', (event) => {{
        if (!dragState) {{
          return;
        }}
        const point = getCalibrationPoint(event.clientX, event.clientY);
        if (!point) {{
          return;
        }}
        writeSelection(buildSelectionFromPoints(dragState.start, point));
      }});

      window.addEventListener('mouseup', (event) => {{
        if (!dragState) {{
          return;
        }}
        const point = getCalibrationPoint(event.clientX, event.clientY);
        if (point) {{
          writeSelection(buildSelectionFromPoints(dragState.start, point));
        }}
        dragState = null;
      }});

      image.addEventListener('load', renderSelectionBox);
      window.addEventListener('resize', renderSelectionBox);

      for (const id of fields) {{
        document.getElementById(id).addEventListener('input', renderSelectionBox);
      }}
    }}

    async function captureCalibration() {{
      if (calibrationBusy) {{
        return;
      }}
      calibrationBusy = true;
      try {{
        const response = await fetch('/api/calibration/capture', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(buildBasePayload())
        }});
        const data = await response.json();
        if (data.error) {{
          document.getElementById('calibration_status').textContent = data.error;
          appendLine('[error] ' + data.error);
          return;
        }}

        calibrationSourceSize = {{
          width: Number(data.source_width || 0),
          height: Number(data.source_height || 0)
        }};
        const image = document.getElementById('calibration_image');
        image.src = data.image_data;
        image.style.display = 'block';
        document.getElementById('calibration_empty').style.display = 'none';
        document.getElementById('selection_box').style.display = 'none';
        document.getElementById('calibration_status').textContent =
          'Desktop captured ' + data.source_width + 'x' + data.source_height + '. Drag on the image to select a region.';
        document.getElementById('template_status').textContent = 'Selection ready for template crop.';
        writeSelection({{ left: 0, top: 0, width: 0, height: 0 }});
      }} catch (error) {{
        document.getElementById('calibration_status').textContent = 'failed to capture desktop';
        appendLine('[error] failed to capture desktop');
      }} finally {{
        calibrationBusy = false;
      }}
    }}

    async function applyCalibrationRegion() {{
      const selection = getSelection();
      if (!hasSelection(selection)) {{
        document.getElementById('calibration_status').textContent = 'Select a region before applying it to the config.';
        return;
      }}

      const payload = buildBasePayload();
      payload.selection_left = selection.left;
      payload.selection_top = selection.top;
      payload.selection_width = selection.width;
      payload.selection_height = selection.height;

      const response = await fetch('/api/calibration/apply-region', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload)
      }});
      const data = await response.json();
      if (data.error) {{
        document.getElementById('calibration_status').textContent = data.error;
        appendLine('[error] ' + data.error);
        return;
      }}

      document.getElementById('calibration_status').textContent =
        'Config updated with ' + describeSelection(selection);
      refreshConfigSummary();
    }}

    async function saveTemplateCrop() {{
      const selection = getSelection();
      if (!hasSelection(selection)) {{
        document.getElementById('template_status').textContent = 'Select a crop region before saving a template.';
        return;
      }}

      const payload = buildBasePayload();
      payload.selection_left = selection.left;
      payload.selection_top = selection.top;
      payload.selection_width = selection.width;
      payload.selection_height = selection.height;
      payload.template_name = document.getElementById('template_name').value;
      payload.template_path = document.getElementById('template_path').value;
      payload.template_threshold = Number(document.getElementById('template_threshold').value || 0.92);
      payload.template_cooldown = Number(document.getElementById('template_cooldown').value || 0.0);
      payload.template_action_type = document.getElementById('template_action_type').value;
      payload.template_action_key = document.getElementById('template_action_key').value;
      payload.template_add_to_config = document.getElementById('template_add_to_config').checked;

      const response = await fetch('/api/calibration/save-template', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload)
      }});
      const data = await response.json();
      if (data.error) {{
        document.getElementById('template_status').textContent = data.error;
        appendLine('[error] ' + data.error);
        return;
      }}

      if (!document.getElementById('template_name').value) {{
        document.getElementById('template_name').value = data.template_name || '';
      }}
      if (!document.getElementById('template_path').value) {{
        document.getElementById('template_path').value = data.template_path || '';
      }}
      document.getElementById('template_status').textContent =
        'Saved ' + (data.template_path || 'template crop') +
        (data.added_to_config ? ' and updated the config.' : '.');
      if (data.added_to_config) {{
        refreshConfigSummary();
      }}
    }}

    async function refreshPreview() {{
      if (previewBusy) {{
        return;
      }}
      previewBusy = true;
      try {{
        const response = await fetch('/api/preview', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(buildBasePayload())
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
        updateLiveSafety(data);
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

    setupCalibrationSelection();
    document.getElementById('config_path').addEventListener('change', refreshConfigSummary);
    refreshConfigSummary();
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
    live_input_armed_until: float = 0.0
    time_func: Callable[[], float] = time.time

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

    def arm_live_input(self, minutes: float = _LIVE_ARM_MINUTES) -> None:
        lifetime = max(0.5, minutes) * 60.0
        self.live_input_armed_until = self.time_func() + lifetime
        self.log(f"[safety] live input armed for {minutes:.1f} minutes")

    def disarm_live_input(self) -> None:
        self.live_input_armed_until = 0.0
        self.log("[safety] live input disarmed")

    def is_live_input_armed(self) -> bool:
        return self.seconds_until_disarm() > 0.0

    def seconds_until_disarm(self) -> float:
        return max(0.0, self.live_input_armed_until - self.time_func())


class WebControlService:
    def __init__(self, default_config_path: str) -> None:
        self.default_config_path = default_config_path
        self.state = WebControlState(log_queue=queue.Queue())
        self.calibration_frame = None

    def write_sample(self, config_path: str) -> None:
        path = write_sample_config(Path(config_path))
        self.state.log(f"[write] sample config created at {path}")

    def config_summary(self, config_path: str) -> dict[str, object]:
        config = AppConfig.load(config_path)
        return {
            "config_path": str(config_path),
            "capture_region": {
                "left": config.capture_region.left,
                "top": config.capture_region.top,
                "width": config.capture_region.width,
                "height": config.capture_region.height,
            },
            "runtime": {
                "interval_seconds": config.runtime.interval_seconds,
                "dry_run": config.runtime.dry_run,
                "max_loops": config.runtime.max_loops,
            },
            "detector_backend": config.detector.backend,
            "template_count": len(config.templates),
            "templates": [
                {
                    "name": item.name,
                    "path": item.path,
                    "threshold": item.threshold,
                    "cooldown_seconds": item.cooldown_seconds,
                    "priority": item.priority,
                    "action_count": len(item.resolved_actions()),
                    "primary_action": item.action.type,
                }
                for item in config.templates
            ],
            "yolo_model_path": config.yolo.model_path,
            "yolo_target_count": len(config.yolo.targets),
            "yolo_targets": [
                {
                    "label": item.label,
                    "min_confidence": item.min_confidence,
                    "cooldown_seconds": item.cooldown_seconds,
                    "priority": item.priority,
                    "action_count": len(item.resolved_actions()),
                    "primary_action": item.action.type,
                }
                for item in config.yolo.targets
            ],
        }

    def arm_live_input(self, phrase: str, minutes: float = _LIVE_ARM_MINUTES) -> dict[str, object]:
        if phrase.strip().upper() != _LIVE_ARM_PHRASE:
            raise RuntimeError(f"Type '{_LIVE_ARM_PHRASE}' exactly to arm live input.")
        self.state.arm_live_input(minutes=minutes)
        return self.safety_status()

    def disarm_live_input(self) -> dict[str, object]:
        self.state.disarm_live_input()
        return self.safety_status()

    def safety_status(self) -> dict[str, object]:
        return {
            "live_input_armed": self.state.is_live_input_armed(),
            "live_input_seconds_left": round(self.state.seconds_until_disarm(), 1),
            "live_arm_phrase": _LIVE_ARM_PHRASE,
        }

    def ensure_live_allowed(self, dry_run: bool) -> None:
        if not dry_run and not self.state.is_live_input_armed():
            raise RuntimeError(
                "Live input is locked. Arm live input in the Safety Lock panel before disabling dry-run."
            )

    def capture_calibration(self) -> dict[str, object]:
        from winvision_macro.calibration import build_calibration_capture_payload
        from winvision_macro.capture import capture_screen

        frame = capture_screen(region=None)
        self.calibration_frame = frame
        payload = build_calibration_capture_payload(frame)
        self.state.log(
            f"[calibration] desktop captured "
            f"{payload['source_width']}x{payload['source_height']}"
        )
        return payload

    def apply_capture_region(
        self,
        config_path: str,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> dict[str, object]:
        from winvision_macro.calibration import CalibrationSelection
        from winvision_macro.config import update_capture_region

        region = CalibrationSelection(left=left, top=top, width=width, height=height).as_region()
        config = update_capture_region(config_path, region)
        self.state.log(
            f"[calibration] capture_region set to "
            f"left={config.capture_region.left} top={config.capture_region.top} "
            f"width={config.capture_region.width} height={config.capture_region.height}"
        )
        return {
            "capture_region": {
                "left": config.capture_region.left,
                "top": config.capture_region.top,
                "width": config.capture_region.width,
                "height": config.capture_region.height,
            }
        }

    def save_template_crop(
        self,
        config_path: str,
        left: int,
        top: int,
        width: int,
        height: int,
        template_name: str,
        template_path: str | None,
        threshold: float,
        cooldown_seconds: float,
        action_type: str,
        action_key: str | None,
        add_to_config: bool,
    ) -> dict[str, object]:
        from winvision_macro.calibration import (
            CalibrationSelection,
            default_template_path,
            save_template_crop,
        )
        from winvision_macro.config import ActionConfig, TemplateConfig, upsert_template

        if self.calibration_frame is None:
            raise RuntimeError("Capture the desktop first before saving a template.")

        name = template_name.strip()
        if not name and not template_path:
            raise RuntimeError("Provide a template name or an explicit template path.")
        if action_type == "press_key" and not (action_key or "").strip():
            raise RuntimeError("Action type 'press_key' needs a key value.")

        region = CalibrationSelection(left=left, top=top, width=width, height=height).as_region()
        destination = Path((template_path or "").strip() or default_template_path(name))
        saved_path = save_template_crop(self.calibration_frame, region, destination)
        template_record_path = saved_path.as_posix()
        self.state.log(f"[template] crop saved to {saved_path}")

        if add_to_config:
            config_template = TemplateConfig(
                name=name or saved_path.stem,
                path=template_record_path,
                threshold=threshold,
                cooldown_seconds=cooldown_seconds,
                action=ActionConfig(type=action_type, key=(action_key or "").strip() or None),
            )
            upsert_template(config_path, config_template)
            self.state.log(
                f"[template] config updated name={config_template.name} "
                f"threshold={config_template.threshold:.2f} action={config_template.action.type}"
            )

        return {
            "template_path": template_record_path,
            "template_name": name or saved_path.stem,
            "added_to_config": add_to_config,
        }

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
        frame_image_path: str | None,
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
            frame_image_path=frame_image_path,
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
        frame_image_path: str | None,
    ) -> None:
        self.ensure_live_allowed(dry_run=dry_run)
        config, runner, controller = build_runtime_stack(
            config_path=config_path,
            dry_run=dry_run,
            interval_seconds=interval_seconds,
            max_loops=max_loops,
            detector_backend=detector_backend,
            yolo_model_path=yolo_model_path,
            yolo_confidence_threshold=yolo_confidence,
            yolo_labels=yolo_labels,
            frame_image_path=frame_image_path,
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
        frame_image_path: str | None,
    ) -> None:
        self.ensure_live_allowed(dry_run=dry_run)
        config, runner, controller = build_runtime_stack(
            config_path=config_path,
            dry_run=dry_run,
            interval_seconds=interval_seconds,
            max_loops=max_loops,
            detector_backend=detector_backend,
            yolo_model_path=yolo_model_path,
            yolo_confidence_threshold=yolo_confidence,
            yolo_labels=yolo_labels,
            frame_image_path=frame_image_path,
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


def _as_int(value: object, default: int = 0) -> int:
    if value in (None, ""):
        return default
    return int(float(value))


def _as_float(value: object, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    return float(value)


def make_handler(service: WebControlService):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_html(_render_page(service.default_config_path))
                return
            if parsed.path == "/api/state":
                payload = {
                    "status": service.state.status,
                    "lines": service.state.take_logs(),
                }
                payload.update(service.safety_status())
                self._send_json(payload)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = _parse_payload(self.rfile.read(length))
            config_path = str(payload.get("config_path", service.default_config_path))
            interval_seconds = _as_float(payload.get("interval_seconds"), 0.35)
            max_loops = _as_int(payload.get("max_loops"), 0)
            dry_run = _as_bool(payload.get("dry_run"), True)
            detector_backend = str(payload.get("detector_backend", "")).strip() or None
            yolo_model_path = str(payload.get("yolo_model_path", "")).strip() or None
            frame_image_path = str(payload.get("frame_image_path", "")).strip() or None
            yolo_confidence_raw = payload.get("yolo_confidence")
            yolo_confidence = _as_float(yolo_confidence_raw) if yolo_confidence_raw not in (None, "") else None
            yolo_labels = _parse_csv_labels(payload.get("yolo_labels"))
            selection_left = _as_int(payload.get("selection_left"), 0)
            selection_top = _as_int(payload.get("selection_top"), 0)
            selection_width = _as_int(payload.get("selection_width"), 0)
            selection_height = _as_int(payload.get("selection_height"), 0)

            if self.path == "/api/write-config":
                service.write_sample(config_path)
                self._send_json({"status": service.state.status or "Ready"})
                return

            if self.path == "/api/config-summary":
                try:
                    data = service.config_summary(config_path)
                except Exception as exc:
                    self._send_json({"status": service.state.status, "error": str(exc)})
                    return
                data["status"] = service.state.status
                data.update(service.safety_status())
                self._send_json(data)
                return

            if self.path == "/api/live/arm":
                try:
                    data = service.arm_live_input(
                        phrase=str(payload.get("live_arm_phrase", "")),
                        minutes=_as_float(payload.get("live_arm_minutes"), _LIVE_ARM_MINUTES),
                    )
                except Exception as exc:
                    self._send_json({"status": service.state.status, "error": str(exc)})
                    return
                data["status"] = service.state.status
                self._send_json(data)
                return

            if self.path == "/api/live/disarm":
                data = service.disarm_live_input()
                data["status"] = service.state.status
                self._send_json(data)
                return

            if self.path == "/api/calibration/capture":
                try:
                    data = service.capture_calibration()
                except Exception as exc:
                    self._send_json({"status": service.state.status, "error": str(exc)})
                    return
                data["status"] = service.state.status
                self._send_json(data)
                return

            if self.path == "/api/calibration/apply-region":
                try:
                    data = service.apply_capture_region(
                        config_path=config_path,
                        left=selection_left,
                        top=selection_top,
                        width=selection_width,
                        height=selection_height,
                    )
                except Exception as exc:
                    self._send_json({"status": service.state.status, "error": str(exc)})
                    return
                data["status"] = service.state.status
                self._send_json(data)
                return

            if self.path == "/api/calibration/save-template":
                try:
                    data = service.save_template_crop(
                        config_path=config_path,
                        left=selection_left,
                        top=selection_top,
                        width=selection_width,
                        height=selection_height,
                        template_name=str(payload.get("template_name", "")),
                        template_path=str(payload.get("template_path", "")).strip() or None,
                        threshold=_as_float(payload.get("template_threshold"), 0.9),
                        cooldown_seconds=_as_float(payload.get("template_cooldown"), 0.0),
                        action_type=str(payload.get("template_action_type", "click_center")).strip() or "click_center",
                        action_key=str(payload.get("template_action_key", "")).strip() or None,
                        add_to_config=_as_bool(payload.get("template_add_to_config"), True),
                    )
                except Exception as exc:
                    self._send_json({"status": service.state.status, "error": str(exc)})
                    return
                data["status"] = service.state.status
                self._send_json(data)
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
                        frame_image_path,
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
                        frame_image_path,
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
                        frame_image_path,
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
