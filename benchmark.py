"""Automated benchmark suite for real-time computer vision and tracking pipeline."""

import os
import time
from typing import List
import cv2
import numpy as np

from core.video_stream import SyntheticStreamGenerator
from core.detector import SyntheticDetector, Detection
from core.tracker import RealTimeMultiTracker
from core.visualizer import Visualizer


def run_benchmark(num_frames: int = 120, output_snapshot: str = "synthetic_snapshot.jpg"):
    print("=" * 72)
    print(" RUNNING COMPUTER VISION PIPELINE PERFORMANCE BENCHMARK")
    print(f" Frames to evaluate: {num_frames}")
    print("=" * 72)

    # Initialize synthetic stream (960x540)
    stream = SyntheticStreamGenerator(width=960, height=540, fps=30)
    detector = SyntheticDetector(conf_threshold=0.40)
    RealTimeMultiTracker.reset_id_counter()
    tracker = RealTimeMultiTracker(iou_threshold=0.30, min_hits=3, max_age=30, max_trail_len=40)
    visualizer = Visualizer(show_trails=True, show_boxes=True, show_hud=True, show_vectors=True)

    det_latencies: List[float] = []
    trk_latencies: List[float] = []
    render_latencies: List[float] = []

    last_annotated_frame = None
    snapshot_captured = False

    t_start = time.perf_counter()

    for frame_idx in range(1, num_frames + 1):
        # Frame ingestion
        ret, frame, gt_boxes = stream.read()
        if not ret:
            break
        detector.set_ground_truth(gt_boxes)

        # 1. Detection
        t0 = time.perf_counter()
        detections: List[Detection] = detector.detect(frame)
        t1 = time.perf_counter()
        det_latencies.append((t1 - t0) * 1000.0)

        # 2. Tracking & State Estimation
        active_tracks = tracker.update(detections)
        t2 = time.perf_counter()
        trk_latencies.append((t2 - t1) * 1000.0)

        # 3. Visualization & HUD
        visualizer.update_fps()
        annotated = visualizer.render(
            frame,
            tracks=active_tracks,
            det_latency_ms=det_latencies[-1],
            trk_latency_ms=trk_latencies[-1],
            source_name="Synthetic Benchmark Stream"
        )
        t3 = time.perf_counter()
        render_latencies.append((t3 - t2) * 1000.0)

        last_annotated_frame = annotated

        # Capture snapshot halfway through when trajectories are rich and active
        if frame_idx == 75 and not snapshot_captured:
            cv2.imwrite(output_snapshot, annotated)
            snapshot_captured = True

    t_end = time.perf_counter()
    total_elapsed = t_end - t_start
    avg_fps = num_frames / total_elapsed if total_elapsed > 0 else 0.0

    if not snapshot_captured and last_annotated_frame is not None:
        cv2.imwrite(output_snapshot, last_annotated_frame)

    avg_det = sum(det_latencies) / len(det_latencies)
    avg_trk = sum(trk_latencies) / len(trk_latencies)
    avg_rnd = sum(render_latencies) / len(render_latencies)
    total_compute_latency = avg_det + avg_trk + avg_rnd

    print("\n" + "=" * 72)
    print(" BENCHMARK RESULTS SCORECARD")
    print("=" * 72)
    print(f" Sustained Processing Speed: {avg_fps:6.1f} FPS")
    print(f" Total Evaluation Duration:  {total_elapsed:6.3f} s ({num_frames} frames)")
    print("-" * 72)
    print(f" Average Detection Latency:  {avg_det:6.2f} ms")
    print(f" Average Tracking Latency:   {avg_trk:6.2f} ms")
    print(f" Average Rendering Latency:  {avg_rnd:6.2f} ms")
    print(f" Total Per-Frame Latency:    {total_compute_latency:6.2f} ms")
    print("-" * 72)
    print(f" Confirmed Tracks Maintained:{tracker.confirmed_tracks_count:6d}")
    print(f" Total Formed Track IDs:     {tracker.total_tracks_count:6d}")
    print(f" Benchmark Snapshot Saved:   {output_snapshot}")
    print("=" * 72)

    return {
        "fps": avg_fps,
        "det_latency_ms": avg_det,
        "trk_latency_ms": avg_trk,
        "rnd_latency_ms": avg_rnd,
        "total_latency_ms": total_compute_latency,
        "tracks_formed": tracker.total_tracks_count,
        "snapshot_path": output_snapshot
    }


if __name__ == "__main__":
    run_benchmark(num_frames=120)
