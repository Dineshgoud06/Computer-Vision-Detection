"""Main entry-point for Real-Time Computer Vision Object Recognition and Tracking application."""

import argparse
import os
import sys
import time
from typing import Optional, List
import cv2
import numpy as np

from core.video_stream import ThreadedVideoCapture, SyntheticStreamGenerator
from core.detector import create_detector, SyntheticDetector, Detection
from core.tracker import RealTimeMultiTracker
from core.visualizer import Visualizer


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Real-Time Object Recognition & Multi-Object Tracking Pipeline (Computer Vision Internship Project)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Stream ingestion
    parser.add_argument(
        "--source",
        type=str,
        default="synthetic",
        help="Input source: 'synthetic' (built-in simulator), '0'/'1' (webcam index), video path (.mp4/.avi), or RTSP URL"
    )

    # Detection & Filtering
    parser.add_argument(
        "--detector",
        type=str,
        default="synthetic",
        choices=["synthetic", "hog", "color", "dnn"],
        help="Detector backend: 'synthetic', 'hog' (pedestrian), 'color' (HSV blob), 'dnn' (OpenCV DNN)"
    )
    parser.add_argument(
        "--classes",
        type=str,
        default=None,
        help="Comma-separated class whitelist to track (e.g. 'car,person,bicycle')"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.40,
        help="Detection confidence threshold [0.0 - 1.0]"
    )
    parser.add_argument(
        "--color-preset",
        type=str,
        default="all",
        choices=["all", "blue", "green", "orange", "red"],
        help="Target color preset when using --detector color"
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=None,
        help="Path to model weights/ONNX file when using --detector dnn"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to model config/prototxt when using --detector dnn"
    )

    # Tracking & State Estimation
    parser.add_argument(
        "--iou",
        type=float,
        default=0.30,
        help="Bipartite Hungarian association IoU gating threshold"
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=30,
        help="Maximum occlusion frames before track deletion"
    )
    parser.add_argument(
        "--min-hits",
        type=int,
        default=3,
        help="Consecutive detections required to confirm track"
    )
    parser.add_argument(
        "--trail-len",
        type=int,
        default=40,
        help="Length of centroid history trail"
    )

    # Output & Recording
    parser.add_argument(
        "--save-video",
        type=str,
        default=None,
        help="Path to save annotated output video (.mp4)"
    )
    parser.add_argument(
        "--snapshot-dir",
        type=str,
        default="snapshots",
        help="Directory to save snapshot captures"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without GUI display window (ideal for servers and automated benchmarks)"
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Limit execution to N frames"
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    print("=" * 72)
    print(" REAL-TIME OBJECT RECOGNITION & MULTI-OBJECT TRACKING PIPELINE")
    print(" Developer: Bajaru Dinesh Goud | Dept of CSE - AI, ML & DS")
    print("=" * 72)
    print(f"[*] Input Source:       {args.source}")
    print(f"[*] Detector Backend:   {args.detector}")
    print(f"[*] Confidence Cutoff:  {args.conf}")
    print(f"[*] Association IoU:    {args.iou}")
    print(f"[*] Occlusion Max-Age:  {args.max_age} frames")
    print(f"[*] Confirmation Hits:  {args.min_hits} frames")
    print(f"[*] Headless Mode:      {args.headless}")
    print("=" * 72)

    # Whitelist parsing
    whitelist = [c.strip().lower() for c in args.classes.split(",")] if args.classes else None

    # Step 1: Initialize Ingestion Stream
    is_synthetic = args.source.lower() in ("synthetic", "sim", "mock")
    stream_gen: Optional[SyntheticStreamGenerator] = None
    stream_cap: Optional[ThreadedVideoCapture] = None

    if is_synthetic:
        stream_gen = SyntheticStreamGenerator(width=960, height=540, fps=30)
        source_name = "Synthetic Road Simulator"
        frame_width, frame_height = stream_gen.width, stream_gen.height
        stream_fps = stream_gen.fps
    else:
        try:
            stream_cap = ThreadedVideoCapture(source=args.source)
            source_name = f"Stream ({args.source})"
            frame_width, frame_height = stream_cap.width, stream_cap.height
            stream_fps = stream_cap.fps
        except Exception as e:
            print(f"[!] ERROR opening video stream: {e}", file=sys.stderr)
            sys.exit(1)

    # Step 2: Initialize Detector Backend
    detector_backend = "synthetic" if is_synthetic else args.detector
    detector = create_detector(
        detector_type=detector_backend,
        conf_threshold=args.conf,
        whitelist=whitelist,
        target_color=args.color_preset,
        weights_path=args.weights,
        config_path=args.config
    )

    # Step 3: Initialize Multi-Object Tracker
    tracker = RealTimeMultiTracker(
        iou_threshold=args.iou,
        max_age=args.max_age,
        min_hits=args.min_hits,
        max_trail_len=args.trail_len
    )

    # Step 4: Initialize Visualizer & Telemetry HUD
    visualizer = Visualizer(
        show_trails=True,
        show_boxes=True,
        show_hud=True,
        show_vectors=True
    )

    # Setup Video Writer if requested
    video_writer: Optional[cv2.VideoWriter] = None
    if args.save_video:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = cv2.VideoWriter(
            args.save_video, fourcc, stream_fps, (frame_width, frame_height)
        )
        print(f"[*] Recording output to: {args.save_video}")

    # Ensure snapshot directory exists
    os.makedirs(args.snapshot_dir, exist_ok=True)

    # Processing state
    frame_idx = 0
    is_paused = False
    window_name = "Real-Time Computer Vision Tracking Telemetry"

    if not args.headless:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, frame_width, frame_height)

    total_proc_time = 0.0
    start_wall_time = time.perf_counter()

    try:
        while True:
            # 1. Grab Frame
            if not is_paused:
                if is_synthetic and stream_gen:
                    ret, raw_frame, gt_boxes = stream_gen.read()
                    if isinstance(detector, SyntheticDetector):
                        detector.set_ground_truth(gt_boxes)
                elif stream_cap:
                    ret, raw_frame = stream_cap.read()
                else:
                    break

                if not ret or raw_frame is None:
                    print("[*] Reached end of video stream or disconnected.")
                    break

                frame_idx += 1

                # 2. Phase 3: Object Detection
                t_det_start = time.perf_counter()
                detections: List[Detection] = detector.detect(raw_frame)
                t_det_end = time.perf_counter()
                det_latency_ms = (t_det_end - t_det_start) * 1000.0

                # 3. Phase 4: Tracking & State Estimation
                t_trk_start = time.perf_counter()
                active_tracks = tracker.update(detections)
                t_trk_end = time.perf_counter()
                trk_latency_ms = (t_trk_end - t_trk_start) * 1000.0

                total_proc_time += (t_trk_end - t_det_start)

            # 4. Phase 5 & 6: Render HUD and Visual Overlays
            visualizer.update_fps()
            annotated_frame = visualizer.render(
                raw_frame,
                tracks=active_tracks if not is_paused else [],
                det_latency_ms=det_latency_ms if not is_paused else 0.0,
                trk_latency_ms=trk_latency_ms if not is_paused else 0.0,
                source_name=source_name,
                is_paused=is_paused
            )

            # Record frame to file if writer active
            if video_writer is not None and not is_paused:
                video_writer.write(annotated_frame)

            # 5. Display GUI / Process User Hotkeys
            if not args.headless:
                cv2.imshow(window_name, annotated_frame)
                key = cv2.waitKey(1 if not is_paused else 30) & 0xFF

                if key in (ord("q"), ord("Q"), 27):  # 'q' or ESC
                    print("[*] User initiated exit.")
                    break
                elif key in (ord("p"), ord("P"), 32):  # 'p' or SPACE
                    is_paused = not is_paused
                    print(f"[*] Stream {'Paused' if is_paused else 'Resumed'}.")
                elif key in (ord("t"), ord("T")):
                    visualizer.show_trails = not visualizer.show_trails
                elif key in (ord("b"), ord("B")):
                    visualizer.show_boxes = not visualizer.show_boxes
                elif key in (ord("h"), ord("H")):
                    visualizer.show_hud = not visualizer.show_hud
                elif key in (ord("s"), ord("S")):
                    snap_name = os.path.join(args.snapshot_dir, f"snapshot_{int(time.time())}.jpg")
                    cv2.imwrite(snap_name, annotated_frame)
                    print(f"[+] Snapshot saved to: {snap_name}")

            # Check max frames constraint
            if args.max_frames and frame_idx >= args.max_frames:
                print(f"[*] Completed {args.max_frames} frames.")
                break

    except KeyboardInterrupt:
        print("\n[*] Interrupted by user.")
    finally:
        # Cleanup resources
        if stream_cap:
            stream_cap.release()
        if stream_gen:
            stream_gen.release()
        if video_writer:
            video_writer.release()
        if not args.headless:
            cv2.destroyAllWindows()

        elapsed_wall = time.perf_counter() - start_wall_time
        avg_fps = frame_idx / elapsed_wall if elapsed_wall > 0 else 0.0
        avg_latency = (total_proc_time / frame_idx * 1000.0) if frame_idx > 0 else 0.0

        print("=" * 72)
        print(" PIPELINE EXECUTION SUMMARY")
        print("=" * 72)
        print(f"Total Frames Processed:   {frame_idx}")
        print(f"Total Elapsed Time:       {elapsed_wall:.2f} s")
        print(f"Average Pipeline Speed:   {avg_fps:.1f} FPS")
        print(f"Average Pipeline Latency: {avg_latency:.2f} ms / frame")
        print(f"Cumulative Tracks Formed: {tracker.total_tracks_count}")
        print("=" * 72)


if __name__ == "__main__":
    main()
