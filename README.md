# Real-Time Object Recognition & Multi-Object Tracking Pipeline

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.0%2B-green.svg)](https://opencv.org)
[![Kalman Filter](https://img.shields.io/badge/Kalman%20Filter-8--State%20Kinematic-orange.svg)](#phase-4-state-estimation--multi-object-tracking-kalman-filter)
[![Data Association](https://img.shields.io/badge/Data%20Association-Hungarian%20SORT-purple.svg)](#bipartite-data-association-hungarian-algorithm)
[![Tests](https://img.shields.io/badge/Unit%20Tests-9%20Passed-brightgreen.svg)](#automated-testing--verification)

> **Capstone & Internship Technical Submission**  
> **Course:** 01AI0510 - Computer Vision & Deep Learning  
> **Author:** Bajaru Dinesh Goud  
> **Department:** Computer Science & Engineering (AI, ML & Data Science)  
> **Institution:** Marwadi University  

---

## 1. Executive Summary & Problem Formulation

In industrial computer vision, detecting objects within single isolated frames is only the first preliminary step. Real-world applications—including **autonomous vehicles, intelligent traffic monitoring, industrial robotics, and security surveillance**—require an automated system to **recognize objects and persistently track their movements over time**, inferring velocity, trajectory, and intent under dynamic real-time constraints.

### Core Engineering Challenges Solved:
1. **Hardware Capture Latency Drift:** Standard `cv2.VideoCapture` uses synchronous internal operating system ring buffers. If downstream neural network inference takes 30ms while the camera runs at 60 FPS (16.6ms), frames queue up in memory, causing cumulative multi-second visual latency drift.
2. **Spatial Deformation During Resizing:** Naive frame resizing introduces severe aspect ratio stretching or squashing, degrading feature representation in deep learning backends.
3. **Identity Switching & Visual Occlusion:** When moving targets cross paths or pass behind environmental obstacles (e.g., pillars, vehicles, overpasses), standard detectors lose the object. The system must maintain continuity and recover identical object IDs upon re-emergence.

---

## 2. End-to-End 6-Stage Computer Vision Pipeline

```
  +-----------------------------------------------------------------------------------+
  |                               VIDEO INGESTION LAYER                               |
  |  Webcam / RTSP / Video / Synthetic Stream -> Thread-Safe Asynchronous Frame Buffer |
  +-----------------------------------------------------------------------------------+
                                            |
                                            v
  +-----------------------------------------------------------------------------------+
  |                                PREPROCESSING LAYER                                |
  |   Aspect-Ratio Letterboxing (r = min(Wt/W, Ht/H)) + Neutral Gray Padding (114)     |
  |   BGR -> RGB Color Space Conversion + Float32 Tensor Normalization [0.0, 1.0]     |
  +-----------------------------------------------------------------------------------+
                                            |
                                            v
  +-----------------------------------------------------------------------------------+
  |                           OBJECT RECOGNITION & FILTERING                          |
  |   Detection Backend: OpenCV DNN / YOLO / HOG-SVM Pedestrians / HSV Color Blobs    |
  |   Class Whitelisting + Confidence Thresholding + Non-Maximum Suppression (NMS)    |
  +-----------------------------------------------------------------------------------+
                                            |
                                            v
  +-----------------------------------------------------------------------------------+
  |                      STATE ESTIMATION & MULTI-OBJECT TRACKING                     |
  |   8-State Linear Kalman Filter: x = [u, v, s, r, du, dv, ds, dr]^T                |
  |   Bipartite Matching: Hungarian Algorithm on Pairwise IoU Cost Matrix (1 - IoU)   |
  |   Finite State Machine: TENTATIVE -> CONFIRMED -> COASTING -> DELETED             |
  +-----------------------------------------------------------------------------------+
                                            |
                                            v
  +-----------------------------------------------------------------------------------+
  |                            MOTION TRAJECTORY ANALYTICS                            |
  |   Centroid History Deque + Sub-Pixel Speed: sqrt(du^2 + dv^2)                     |
  |   Dynamic Progressive Fading Comet Trails + Directional Heading Vector Arrows     |
  +-----------------------------------------------------------------------------------+
                                            |
                                            v
  +-----------------------------------------------------------------------------------+
  |                            TELEMETRY HUD & VISUALIZATION                          |
  |   Glassmorphism HUD Banner (Real-Time FPS, Latency Breakdown, Track Counters)    |
  |   Golden-Ratio Color Hashing per Track ID + Corner-Bracket Bounding Boxes         |
  |   Real-Time Video Recording (.mp4) + High-Resolution Snapshot Capture             |
  +-----------------------------------------------------------------------------------+
```

---

### Detailed Stage Breakdown

#### Phase 1: Video Ingestion & Asynchronous Decoupling (`core/video_stream.py`)
- **Threaded Frame Acquisition:** Implements `ThreadedVideoCapture`, running an isolated daemon worker thread that continuously polls hardware buffers at native sensor refresh rates.
- **Zero-Lag Atomic Buffering:** Uses a thread lock (`threading.Lock`) that overwrites unconsumed frames, discarding obsolete queued buffer frames and guaranteeing that the vision pipeline always operates on the newest real-time frame.
- **Built-in Synthetic Stream Generator (`SyntheticStreamGenerator`):** Provides a high-fidelity synthetic traffic simulator generating moving vehicles, crossing pedestrians, and stationary occlusion pillars. This allows evaluators and interviewers to run and verify the complete tracking pipeline without requiring a physical camera or video files.

#### Phase 2: Aspect-Ratio Preserving Letterboxing (`core/preprocessor.py`)
- **Uniform Scaling:**
  $$\text{scale } r = \min\left(\frac{W_{\text{target}}}{W_{\text{orig}}}, \frac{H_{\text{target}}}{H_{\text{orig}}}\right)$$
- **Symmetric Padding:** Computes margin offsets $dw = (W_{\text{target}} - W_{\text{unpad}})/2$ and $dh = (H_{\text{target}} - H_{\text{unpad}})/2$, filling border margins with neutral gray `(114, 114, 114)` to prevent distortion.
- **Inverse Coordinate Projection:** Detections in letterbox space are mapped back to native frame space via:
  $$x_{\text{orig}} = \frac{x' - dw}{r}, \quad y_{\text{orig}} = \frac{y' - dh}{r}$$

#### Phase 3: Object Recognition & Redundancy Suppression (`core/detector.py`)
- **Multi-Backend Support:**
  - **OpenCV DNN:** Forward passes ONNX / YOLO / MobileNet-SSD deep models.
  - **HOG + Linear SVM:** Real-world pedestrian detection using OpenCV's built-in `HOGDescriptor_getDefaultPeopleDetector()`.
  - **HSV Color Segmentation:** Classical computer vision blob detection using Hue-Saturation-Value color thresholding and morphological filtering (`cv2.morphologyEx`).
  - **Synthetic Detector:** Ground-truth detection generator with realistic sensor noise for benchmarking.
- **Class Whitelisting:** User-configurable target filters (e.g. `--classes person,car`) discard irrelevant background classes before entering the tracker.
- **Non-Maximum Suppression (NMS):** Eliminates duplicate bounding boxes from multi-scale feature grids:
  $$\text{IoU}(A, B) = \frac{\text{Area}(A \cap B)}{\text{Area}(A \cup B)}$$
  Boxes exceeding an IoU threshold of 0.45 are pruned in descending order of confidence.

#### Phase 4: State Estimation & Multi-Object Tracking (`core/kalman_filter.py`, `core/tracker.py`)
- **8-State Kinematic Motion Space:** Each target is modeled in continuous 2D space:
  $$\mathbf{x} = \begin{bmatrix} u & v & s & r & \dot{u} & \dot{v} & \dot{s} & \dot{r} \end{bmatrix}^T$$
  - $u, v$: Horizontal and vertical bounding box centroid coordinates
  - $s$: Scale / Area ($w \cdot h$)
  - $r$: Aspect ratio ($w / h$)
  - $\dot{u}, \dot{v}, \dot{s}, \dot{r}$: First-order kinematic velocity derivatives
- **Observation Model:**
  $$\mathbf{z} = \begin{bmatrix} u & v & s & r \end{bmatrix}^T, \quad \mathbf{H} = \begin{bmatrix} \mathbf{I}_{4 \times 4} & \mathbf{0}_{4 \times 4} \end{bmatrix}$$
- **Kalman Predict-Update Cycle:**
  1. *A Priori Prediction:*
     $$\hat{\mathbf{x}}_{k|k-1} = \mathbf{F} \hat{\mathbf{x}}_{k-1|k-1}, \quad \mathbf{P}_{k|k-1} = \mathbf{F}\mathbf{P}_{k-1|k-1}\mathbf{F}^T + \mathbf{Q}$$
  2. *Innovation & Residual Covariance:*
     $$\mathbf{y}_k = \mathbf{z}_k - \mathbf{H}\hat{\mathbf{x}}_{k|k-1}, \quad \mathbf{S}_k = \mathbf{H}\mathbf{P}_{k|k-1}\mathbf{H}^T + \mathbf{R}$$
  3. *A Posteriori Correction:*
     $$\mathbf{K}_k = \mathbf{P}_{k|k-1}\mathbf{H}^T \mathbf{S}_k^{-1}, \quad \hat{\mathbf{x}}_{k|k} = \hat{\mathbf{x}}_{k|k-1} + \mathbf{K}_k \mathbf{y}_k, \quad \mathbf{P}_{k|k} = (\mathbf{I} - \mathbf{K}_k\mathbf{H})\mathbf{P}_{k|k-1}$$
- **Bipartite Data Association (Hungarian Algorithm):**
  - Pairwise Cost Matrix: $\mathbf{C}_{i, j} = 1 - \text{IoU}(\text{det}_i, \text{track}_j)$.
  - Solves global minimum cost bipartite assignment in polynomial time $O(N^3)$.
  - Rejects matches failing the spatial gating threshold ($\text{IoU} < 0.30$).
- **Track Lifecycle State Machine:**
  - `TENTATIVE`: Initialized upon new detection; requires `min_hits` (default 3) consecutive detections to filter false positives.
  - `CONFIRMED`: Actively visible, rendered on screen with persistent Track ID.
  - `COASTING / LOST`: Forward-projected solely via Kalman filter during occlusions (up to `max_age = 30` frames).
  - `OCCLUSION RECOVERY`: When the object emerges, Hungarian matching re-associates it to its original Track ID.
  - `DELETED`: Pruned from memory once age exceeds threshold.

#### Phase 5: Motion Trajectory Analytics (`core/visualizer.py`)
- **Centroid History Queue:** Bounded FIFO `collections.deque(maxlen=40)` storing smoothed center points.
- **Progressive Fading Comet Tails:** Polyline segments rendered with decaying width and opacity:
  $$\text{thickness}(i) = \max\left(1, \left\lfloor 3.5 \cdot \frac{i}{N_{\text{trail}}} \right\rfloor\right)$$
- **Sub-Pixel Speed & Heading:** Computes filtered instantaneous speed $\text{speed} = \sqrt{\dot{u}^2 + \dot{v}^2}$ and renders directional heading arrows pointing along the velocity vector.

#### Phase 6: Telemetry Heads-Up Display (HUD) Overlay (`core/visualizer.py`)
- **Glassmorphic Telemetry HUD:** Semi-transparent top banner displaying real-time FPS, active track count, coasting count, detection latency (ms), and tracking latency (ms).
- **Golden-Ratio Color Hashing:** Assigns 100 visually distinct, repeatable BGR colors based on Track ID:
  $$H_k = (0.1 + k \cdot 0.618033988749895) \bmod 1.0$$
- **Corner-Bracket Cyber Bounding Boxes:** Modern corner accents with translucent badge overlays showing `#ID Class Confidence% Speed`.

---

## 3. Project Directory Structure

```
Antigravity/
├── core/
│   ├── __init__.py           # Package exports and version metadata
│   ├── video_stream.py       # ThreadedVideoCapture and SyntheticStreamGenerator
│   ├── preprocessor.py       # Aspect-ratio letterboxing, normalization, unpadding
│   ├── detector.py           # Multi-backend detectors (DNN, HOG, HSV Color, Synthetic)
│   ├── kalman_filter.py      # 8-state Linear Kalman Filter kinematic motion model
│   ├── tracker.py            # RealTimeMultiTracker, Hungarian association, FSM lifecycle
│   └── visualizer.py         # Telemetry HUD, fading comet trails, direction vectors
├── app.py                    # Main CLI application with interactive hotkeys
├── benchmark.py              # Automated performance benchmark and latency scorecard
├── test_tracker.py           # Comprehensive 9-test unit test suite
├── requirements.txt          # Project dependencies
├── synthetic_snapshot.jpg    # Output snapshot from empirical benchmark
├── RealTime_Object_Recognition_and_Tracking_University_Format.pptx  # Capstone Presentation
└── README.md                 # Production-grade technical report & documentation
```

---

## 4. Quickstart & Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application

#### Option A: Built-in Synthetic Simulator (Recommended for instant testing)
Runs the complete multi-object tracking pipeline with simulated moving vehicles, pedestrians, and an occlusion pillar:
```bash
python app.py --source synthetic
```

#### Option B: Live Webcam Stream
Track real-world objects using your connected webcam:
```bash
python app.py --source 0 --detector color --color-preset blue
```
*(Tracks blue objects, pens, cups, or markers with full trajectory trails)*

#### Option C: Pedestrian Detection on Video File
Run the built-in OpenCV HOG + Linear SVM detector on a video file:
```bash
python app.py --source walking.mp4 --detector hog --classes person
```

#### Option D: OpenCV Deep Neural Network (YOLOv8 / ONNX)
Run high-performance deep learning inference:
```bash
python app.py --source video.mp4 --detector dnn --weights yolov8n.onnx
```

#### Option E: Save Annotated Output Video
```bash
python app.py --source synthetic --save-video tracked_output.mp4 --max-frames 300
```

---

## 5. Interactive Keyboard Shortcuts

When the application is running in GUI mode, you can control the visualization in real time:

| Hotkey | Action | Description |
|:---:|:---|:---|
| **`Q` / `ESC`** | **Exit** | Cleanly terminates threads, closes windows, and releases resources |
| **`SPACE` / `P`** | **Pause / Resume** | Freezes the video stream while preserving track state |
| **`T`** | **Toggle Trails** | Enables or disables historical comet motion trails |
| **`B`** | **Toggle Boxes** | Shows or hides bounding boxes and corner brackets |
| **`H`** | **Toggle HUD** | Toggles the top glassmorphism telemetry banner |
| **`S`** | **Save Snapshot** | Saves high-resolution annotated frame to `./snapshots/` |

---

## 6. Empirical Benchmarks & Verification

### Performance Scorecard (Synthetic 960x540 Benchmark on CPU)
Evaluated across 120 continuous frames with crossing paths and full visual occlusion:

| Performance Metric | Measured Value | Target Criterion | Status |
|:---|:---:|:---:|:---:|
| **Sustained Throughput** | **84.3 FPS** | > 30.0 FPS | PASS |
| **Average Detection Latency** | **0.02 ms** | < 15.0 ms | PASS |
| **Average Tracking Latency** | **1.10 ms** | < 5.0 ms | PASS |
| **Average Rendering Latency** | **8.96 ms** | < 10.0 ms | PASS |
| **Total Pipeline Latency** | **10.08 ms** | < 33.3 ms | PASS |
| **Active Tracks Maintained** | **3 of 3** | 3 Targets | PASS |
| **Identity Switches Across Occlusion**| **0 Switches** | 0 Switches | PASS |

### Automated Unit Test Suite (`test_tracker.py`)
Run the test suite:
```bash
python test_tracker.py
```
**Output:**
```
test_bbox_z_roundtrip (__main__.TestBoundingBoxAndMath.test_bbox_z_roundtrip) ... ok
test_iou_disjoint_boxes (__main__.TestBoundingBoxAndMath.test_iou_disjoint_boxes) ... ok
test_iou_identical_boxes (__main__.TestBoundingBoxAndMath.test_iou_identical_boxes) ... ok
test_iou_partial_overlap (__main__.TestBoundingBoxAndMath.test_iou_partial_overlap) ... ok
test_nms_suppression (__main__.TestBoundingBoxAndMath.test_nms_suppression) ... ok
test_kalman_constant_velocity_tracking (__main__.TestKalmanFilter.test_kalman_constant_velocity_tracking) ... ok
test_letterbox_and_restore (__main__.TestPreprocessor.test_letterbox_and_restore) ... ok
test_fsm_confirmation_lifecycle (__main__.TestTrackerLifecycleAndOcclusion.test_fsm_confirmation_lifecycle) ... ok
test_occlusion_recovery_preserves_id (__main__.TestTrackerLifecycleAndOcclusion.test_occlusion_recovery_preserves_id) ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.038s

OK
```

---

## 7. Internship Technical Viva & Interview Preparation

### Q1: Why use an 8-state Kalman Filter instead of simple centroid Euclidean distance?
**Answer:** Simple centroid distance tracking fails when objects accelerate, change aspect ratio, or become occluded. The 8-state Kalman Filter ($u, v, s, r, \dot{u}, \dot{v}, \dot{s}, \dot{r}$) estimates continuous velocity and scale dynamics. Even during total occlusion (when zero measurements arrive), the motion model forward-projects the target's expected trajectory, enabling reliable re-association when it emerges.

### Q2: How does the Hungarian Algorithm solve data association?
**Answer:** Data association between $M$ detections and $N$ active tracks forms a weighted bipartite matching problem. Greedy nearest-neighbor matching often causes race conditions and wrong associations when objects cross paths. The Hungarian (Munkres) algorithm computes the globally optimal assignment minimizing the total cost matrix $\mathbf{C}_{i,j} = 1 - \text{IoU}(i, j)$ in polynomial time $O(N^3)$.

### Q3: Why is asynchronous threaded video capture essential for real-time applications?
**Answer:** Default OpenCV `cv2.VideoCapture.read()` is synchronous. If the computer vision pipeline takes 35ms per frame while the camera produces 60 FPS (16.6ms), frames accumulate inside the driver's ring buffer. After 1 minute of streaming, the displayed stream lags several seconds behind reality. Our `ThreadedVideoCapture` continuously consumes camera frames in a background thread and holds only the latest frame in an atomic lock, eliminating lag drift.

### Q4: How does letterboxing prevent model degradation?
**Answer:** Directly squeezing a 16:9 widescreen frame (e.g. 1920x1080) into a square 640x640 input distorts the geometric aspect ratios of objects (cars become tall and narrow, pedestrians become wide). Letterboxing preserves the true aspect ratio using uniform scaling $r = \min(640/1920, 640/1080)$, padding the remaining margins with neutral gray `(114, 114, 114)` and cleanly projecting detected coordinates back to original resolution.

---

## 8. License & Acknowledgments

Developed as part of the **Computer Vision & Deep Learning Capstone Project** by **Bajaru Dinesh Goud** at **Marwadi University**. Released under the MIT Open Source License.
