"""Web Application Dashboard for Real-Time Object Recognition and Tracking.
Zero external server dependencies (uses Python built-in ThreadingHTTPServer).
Serves live MJPEG stream, interactive controls, telemetry metrics, and snapshot gallery.
"""

import http.server
import io
import json
import os
import sys
import threading
import time
import urllib.parse
import webbrowser
from typing import Optional, List
import cv2
import numpy as np

from core.video_stream import ThreadedVideoCapture, SyntheticStreamGenerator
from core.detector import create_detector, SyntheticDetector, Detection
from core.tracker import RealTimeMultiTracker
from core.visualizer import Visualizer


# Global Web State
class AppState:
    def __init__(self):
        self.lock = threading.Lock()
        self.running = True
        self.paused = False
        
        # Stream & Detector configuration
        self.source_type = "synthetic"  # "synthetic" or "webcam"
        self.stream_gen: Optional[SyntheticStreamGenerator] = SyntheticStreamGenerator(width=960, height=540, fps=30)
        self.stream_cap: Optional[ThreadedVideoCapture] = None
        
        self.detector = create_detector(detector_type="synthetic", conf_threshold=0.40)
        self.tracker = RealTimeMultiTracker(iou_threshold=0.30, min_hits=3, max_age=30, max_trail_len=40)
        self.visualizer = Visualizer(show_trails=True, show_boxes=True, show_hud=True, show_vectors=True)
        
        # Telemetry
        self.current_fps = 0.0
        self.det_latency = 0.0
        self.trk_latency = 0.0
        self.active_tracks_count = 0
        self.coasting_tracks_count = 0
        self.total_frames = 0
        self.current_frame_jpeg: Optional[bytes] = None
        self.snapshots: List[str] = []

    def set_source(self, source_name: str):
        with self.lock:
            if source_name == self.source_type:
                return

            if self.stream_cap:
                self.stream_cap.release()
                self.stream_cap = None
            if self.stream_gen:
                self.stream_gen.release()
                self.stream_gen = None

            RealTimeMultiTracker.reset_id_counter()
            self.tracker = RealTimeMultiTracker(iou_threshold=0.30, min_hits=3, max_age=30)

            if source_name == "webcam":
                try:
                    self.stream_cap = ThreadedVideoCapture(source=0)
                    self.detector = create_detector(detector_type="color", conf_threshold=0.45, target_color="blue")
                    self.source_type = "webcam"
                except Exception as e:
                    print(f"[!] Could not open webcam, reverting to synthetic: {e}")
                    self.stream_gen = SyntheticStreamGenerator(width=960, height=540, fps=30)
                    self.detector = create_detector(detector_type="synthetic", conf_threshold=0.40)
                    self.source_type = "synthetic"
            else:
                self.stream_gen = SyntheticStreamGenerator(width=960, height=540, fps=30)
                self.detector = create_detector(detector_type="synthetic", conf_threshold=0.40)
                self.source_type = "synthetic"

    def take_snapshot(self) -> str:
        with self.lock:
            if self.current_frame_jpeg is None:
                return ""
            os.makedirs("snapshots", exist_ok=True)
            filename = f"web_snap_{int(time.time())}.jpg"
            filepath = os.path.join("snapshots", filename)
            with open(filepath, "wb") as f:
                f.write(self.current_frame_jpeg)
            self.snapshots.append(filename)
            return filename


state = AppState()


def processing_worker():
    """Background worker thread that runs continuous computer vision inference."""
    while state.running:
        if state.paused:
            time.sleep(0.05)
            continue

        with state.lock:
            if state.source_type == "synthetic" and state.stream_gen:
                ret, raw_frame, gt = state.stream_gen.read()
                if isinstance(state.detector, SyntheticDetector):
                    state.detector.set_ground_truth(gt)
            elif state.stream_cap:
                ret, raw_frame = state.stream_cap.read()
            else:
                ret, raw_frame = False, None

        if not ret or raw_frame is None:
            time.sleep(0.01)
            continue

        state.total_frames += 1

        # 1. Detection
        t0 = time.perf_counter()
        detections = state.detector.detect(raw_frame)
        t1 = time.perf_counter()
        state.det_latency = (t1 - t0) * 1000.0

        # 2. Tracking
        t2 = time.perf_counter()
        active_tracks = state.tracker.update(detections)
        t3 = time.perf_counter()
        state.trk_latency = (t3 - t2) * 1000.0

        state.active_tracks_count = state.tracker.confirmed_tracks_count
        state.coasting_tracks_count = state.tracker.coasting_tracks_count

        # 3. Render
        state.current_fps = state.visualizer.update_fps()
        src_label = "Synthetic Stream" if state.source_type == "synthetic" else "Webcam (HSV Tracker)"
        annotated = state.visualizer.render(
            raw_frame,
            tracks=active_tracks,
            det_latency_ms=state.det_latency,
            trk_latency_ms=state.trk_latency,
            source_name=src_label
        )

        # Encode to JPEG
        _, jpeg = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        with state.lock:
            state.current_frame_jpeg = jpeg.tobytes()

        # Moderate loop frame rate
        time.sleep(0.005)


HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionStream AI - Real-Time Object Recognition & Tracking</title>
    <style>
        :root {
            --bg-dark: #0f141c;
            --card-bg: #18202c;
            --card-border: #283446;
            --accent-cyan: #00d2ff;
            --accent-blue: #0070c0;
            --accent-green: #10b981;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg-dark); color: var(--text-main); min-height: 100vh; display: flex; flex-direction: column; }
        
        /* Header */
        header {
            background: linear-gradient(90deg, #131b26, #1c2636);
            border-bottom: 2px solid var(--accent-cyan);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .brand { display: flex; align-items: center; gap: 12px; }
        .logo-badge {
            background: var(--accent-cyan);
            color: #000;
            font-weight: 800;
            font-size: 1.25rem;
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .brand-title { font-size: 1.25rem; font-weight: 700; color: #fff; }
        .brand-subtitle { font-size: 0.8rem; color: var(--text-muted); }
        .author-tag { font-size: 0.85rem; color: var(--accent-cyan); background: rgba(0, 210, 255, 0.1); padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(0, 210, 255, 0.3); }

        /* Container */
        .main-container {
            display: grid;
            grid-template-columns: 1fr 340px;
            gap: 1.5rem;
            padding: 1.5rem 2rem;
            flex: 1;
        }

        /* Stream Card */
        .stream-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }
        .stream-header {
            padding: 0.8rem 1.2rem;
            background: rgba(255,255,255,0.02);
            border-bottom: 1px solid var(--card-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .live-badge {
            display: flex;
            align-items: center;
            gap: 6px;
            color: var(--accent-green);
            font-size: 0.85rem;
            font-weight: 600;
        }
        .pulse-dot {
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }
        
        .video-wrapper {
            position: relative;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 480px;
        }
        .video-wrapper img {
            width: 100%;
            height: auto;
            max-height: 600px;
            object-fit: contain;
            display: block;
        }

        /* Sidebar Controls & Stats */
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
        }
        .stat-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.8rem;
        }
        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
        }
        .stat-value { font-size: 1.6rem; font-weight: 700; color: var(--accent-cyan); margin-bottom: 4px; }
        .stat-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }

        .control-panel {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 1.2rem;
        }
        .panel-title {
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 0.5rem;
            color: #fff;
        }
        .btn-group { display: flex; flex-direction: column; gap: 0.6rem; }
        .btn {
            background: #222d3e;
            color: #fff;
            border: 1px solid var(--card-border);
            padding: 0.65rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.2s ease;
        }
        .btn:hover { background: #2c3a50; border-color: var(--accent-cyan); }
        .btn.active { background: rgba(0, 210, 255, 0.15); border-color: var(--accent-cyan); color: var(--accent-cyan); }
        .btn-action {
            background: var(--accent-cyan);
            color: #0b1118;
            font-weight: 700;
            border: none;
            justify-content: center;
            margin-top: 0.5rem;
        }
        .btn-action:hover { background: #38e1ff; }

        /* Footer */
        footer {
            background: #0b1017;
            padding: 1rem 2rem;
            font-size: 0.8rem;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
            border-top: 1px solid var(--card-border);
        }
        a { color: var(--accent-cyan); text-decoration: none; }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <div class="logo-badge">V</div>
            <div>
                <div class="brand-title">VisionStream AI</div>
                <div class="brand-subtitle">Real-Time Object Recognition & Multi-Object Tracking Pipeline</div>
            </div>
        </div>
        <div class="author-tag">Bajaru Dinesh Goud | Capstone Project</div>
    </header>

    <div class="main-container">
        <!-- Live Video Area -->
        <div class="stream-card">
            <div class="stream-header">
                <div class="live-badge">
                    <div class="pulse-dot"></div>
                    <span id="stream-status">LIVE TELEMETRY STREAM</span>
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">
                    Resolution: <span style="color: #fff;">960 x 540</span>
                </div>
            </div>
            <div class="video-wrapper">
                <img src="/video_feed" alt="Real-Time Computer Vision Tracking Stream" id="video-stream">
            </div>
        </div>

        <!-- Sidebar Controls & Metrics -->
        <div class="sidebar">
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-value" id="fps-val">--</div>
                    <div class="stat-label">Pipeline FPS</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="tracks-val">--</div>
                    <div class="stat-label">Active Tracks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="det-lat-val">--</div>
                    <div class="stat-label">Detection Latency</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="trk-lat-val">--</div>
                    <div class="stat-label">Tracking Latency</div>
                </div>
            </div>

            <!-- Interactive Control Panel -->
            <div class="control-panel">
                <div class="panel-title">Stream Source</div>
                <div class="btn-group">
                    <button class="btn active" id="btn-synthetic" onclick="setSource('synthetic')">
                        <span>Synthetic Simulator</span>
                        <span>[Crossing + Pillar]</span>
                    </button>
                    <button class="btn" id="btn-webcam" onclick="setSource('webcam')">
                        <span>Webcam Feed</span>
                        <span>[Live HSV Tracker]</span>
                    </button>
                </div>
            </div>

            <div class="control-panel">
                <div class="panel-title">Visual Overlays</div>
                <div class="btn-group">
                    <button class="btn active" id="btn-trails" onclick="toggleOption('trails')">
                        <span>Comet Motion Trails</span>
                        <span id="badge-trails">ON</span>
                    </button>
                    <button class="btn active" id="btn-boxes" onclick="toggleOption('boxes')">
                        <span>Corner Bounding Boxes</span>
                        <span id="badge-boxes">ON</span>
                    </button>
                    <button class="btn active" id="btn-hud" onclick="toggleOption('hud')">
                        <span>Glassmorphic HUD</span>
                        <span id="badge-hud">ON</span>
                    </button>
                    <button class="btn" id="btn-pause" onclick="toggleOption('pause')">
                        <span id="label-pause">Pause Stream</span>
                        <span>[SPACE]</span>
                    </button>
                    <button class="btn btn-action" onclick="captureSnapshot()">
                        Capture Snapshot [S]
                    </button>
                </div>
            </div>
        </div>
    </div>

    <footer>
        <div>Department of CSE (AI, ML & DS) &bull; Marwadi University</div>
        <div>Pipeline: <strong>8-State Kalman Filter + Hungarian Bipartite Association</strong></div>
    </footer>

    <script>
        // Poll telemetry metrics every 500ms
        async function updateStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                document.getElementById('fps-val').innerText = data.fps.toFixed(1);
                document.getElementById('tracks-val').innerText = data.active_tracks;
                document.getElementById('det-lat-val').innerText = data.det_latency.toFixed(1) + 'ms';
                document.getElementById('trk-lat-val').innerText = data.trk_latency.toFixed(1) + 'ms';
            } catch (err) {
                console.error("Telemetry fetch error:", err);
            }
        }
        setInterval(updateStats, 500);

        async function setSource(src) {
            await fetch('/api/control?action=set_source&source=' + src);
            document.getElementById('btn-synthetic').classList.toggle('active', src === 'synthetic');
            document.getElementById('btn-webcam').classList.toggle('active', src === 'webcam');
        }

        async function toggleOption(opt) {
            const res = await fetch('/api/control?action=toggle_' + opt);
            const data = await res.json();
            if (opt === 'trails') {
                document.getElementById('badge-trails').innerText = data.show_trails ? 'ON' : 'OFF';
                document.getElementById('btn-trails').classList.toggle('active', data.show_trails);
            } else if (opt === 'boxes') {
                document.getElementById('badge-boxes').innerText = data.show_boxes ? 'ON' : 'OFF';
                document.getElementById('btn-boxes').classList.toggle('active', data.show_boxes);
            } else if (opt === 'hud') {
                document.getElementById('badge-hud').innerText = data.show_hud ? 'ON' : 'OFF';
                document.getElementById('btn-hud').classList.toggle('active', data.show_hud);
            } else if (opt === 'pause') {
                document.getElementById('label-pause').innerText = data.paused ? 'Resume Stream' : 'Pause Stream';
                document.getElementById('btn-pause').classList.toggle('active', data.paused);
            }
        }

        async function captureSnapshot() {
            const res = await fetch('/api/control?action=snapshot');
            const data = await res.json();
            alert("Snapshot captured successfully: " + data.filename);
        }

        // Global hotkeys
        window.addEventListener('keydown', (e) => {
            if (e.code === 'Space') toggleOption('pause');
            if (e.key === 't' || e.key === 'T') toggleOption('trails');
            if (e.key === 'b' || e.key === 'B') toggleOption('boxes');
            if (e.key === 'h' || e.key === 'H') toggleOption('hud');
            if (e.key === 's' || e.key === 'S') captureSnapshot();
        });
    </script>
</body>
</html>
"""


class VisionDashboardHandler(http.server.BaseHTTPRequestHandler):
    """Custom HTTP handler serving the live MJPEG stream and control endpoints."""

    def log_message(self, format, *args):
        # Suppress spammy HTTP access logs in console
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # 1. Main Dashboard HTML
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))

        # 2. Real-Time MJPEG Video Feed
        elif path == "/video_feed":
            self.send_response(200)
            self.send_header("Age", "0")
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
            self.end_headers()

            try:
                while state.running:
                    with state.lock:
                        jpeg_bytes = state.current_frame_jpeg

                    if jpeg_bytes is not None:
                        self.wfile.write(b"--FRAME\r\n")
                        self.send_header("Content-Type", "image/jpeg")
                        self.send_header("Content-Length", str(len(jpeg_bytes)))
                        self.end_headers()
                        self.wfile.write(jpeg_bytes)
                        self.wfile.write(b"\r\n")

                    time.sleep(0.033)  # ~30 FPS stream to client
            except (ConnectionResetError, BrokenPipeError):
                pass

        # 3. Telemetry JSON API
        elif path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload = {
                "fps": state.current_fps,
                "active_tracks": state.active_tracks_count,
                "coasting_tracks": state.coasting_tracks_count,
                "det_latency": state.det_latency,
                "trk_latency": state.trk_latency,
                "total_frames": state.total_frames,
                "source": state.source_type
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        # 4. Interactive Control Endpoints
        elif path == "/api/control":
            action = params.get("action", [""])[0]
            resp_data = {"status": "ok"}

            if action == "toggle_trails":
                state.visualizer.show_trails = not state.visualizer.show_trails
                resp_data["show_trails"] = state.visualizer.show_trails
            elif action == "toggle_boxes":
                state.visualizer.show_boxes = not state.visualizer.show_boxes
                resp_data["show_boxes"] = state.visualizer.show_boxes
            elif action == "toggle_hud":
                state.visualizer.show_hud = not state.visualizer.show_hud
                resp_data["show_hud"] = state.visualizer.show_hud
            elif action == "toggle_pause":
                state.paused = not state.paused
                resp_data["paused"] = state.paused
            elif action == "set_source":
                new_src = params.get("source", ["synthetic"])[0]
                state.set_source(new_src)
                resp_data["source"] = state.source_type
            elif action == "snapshot":
                filename = state.take_snapshot()
                resp_data["filename"] = filename

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp_data).encode("utf-8"))

        else:
            self.send_error(404, "Page Not Found")


def launch_web_server(port: int = 5000, open_browser: bool = True):
    # Start CV processing thread
    cv_thread = threading.Thread(target=processing_worker, daemon=True)
    cv_thread.start()

    server_address = ("", port)
    # Using ThreadingHTTPServer so simultaneous MJPEG streaming and JSON calls don't block
    httpd = http.server.ThreadingHTTPServer(server_address, VisionDashboardHandler)

    url = f"http://localhost:{port}"
    print("=" * 72)
    print(" VISIONSTREAM-AI WEB DASHBOARD STARTED")
    print("=" * 72)
    print(f"[*] Access the Web Application at: {url}")
    print(f"[*] Press CTRL+C to stop the web server")
    print("=" * 72)

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down web server...")
    finally:
        state.running = False
        httpd.server_close()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 5000
    launch_web_server(port=port_arg, open_browser=True)
