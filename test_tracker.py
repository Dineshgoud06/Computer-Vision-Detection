"""Unit test suite for Computer Vision and Multi-Object Tracking Pipeline."""

import unittest
import numpy as np

from core.kalman_filter import KalmanBoxTracker, bbox_to_z, x_to_bbox
from core.detector import Detection, compute_iou, non_max_suppression
from core.tracker import RealTimeMultiTracker, Track, TrackState
from core.preprocessor import Preprocessor


class TestBoundingBoxAndMath(unittest.TestCase):
    """Test geometric conversions and IoU computations."""

    def test_bbox_z_roundtrip(self):
        original_box = [100.0, 150.0, 200.0, 350.0]  # w=100, h=200, u=150, v=250, s=20000, r=0.5
        z = bbox_to_z(original_box)
        self.assertAlmostEqual(z[0, 0], 150.0)
        self.assertAlmostEqual(z[1, 0], 250.0)
        self.assertAlmostEqual(z[2, 0], 20000.0)
        self.assertAlmostEqual(z[3, 0], 0.5)

        # Convert back
        recovered_box = x_to_bbox(z)
        self.assertAlmostEqual(original_box[0], recovered_box[0], places=3)
        self.assertAlmostEqual(original_box[1], recovered_box[1], places=3)
        self.assertAlmostEqual(original_box[2], recovered_box[2], places=3)
        self.assertAlmostEqual(original_box[3], recovered_box[3], places=3)

    def test_iou_identical_boxes(self):
        box_a = [50.0, 50.0, 150.0, 150.0]
        box_b = [50.0, 50.0, 150.0, 150.0]
        iou = compute_iou(box_a, box_b)
        self.assertAlmostEqual(iou, 1.0, places=4)

    def test_iou_disjoint_boxes(self):
        box_a = [0.0, 0.0, 50.0, 50.0]
        box_b = [100.0, 100.0, 150.0, 150.0]
        iou = compute_iou(box_a, box_b)
        self.assertEqual(iou, 0.0)

    def test_iou_partial_overlap(self):
        box_a = [0.0, 0.0, 100.0, 100.0]      # area = 10,000
        box_b = [50.0, 0.0, 150.0, 100.0]     # area = 10,000, inter = 5,000, union = 15,000
        iou = compute_iou(box_a, box_b)
        self.assertAlmostEqual(iou, 5000.0 / 15000.0, places=4)

    def test_nms_suppression(self):
        boxes = [
            [10.0, 10.0, 100.0, 100.0],
            [12.0, 11.0, 101.0, 99.0],   # Heavily overlapping duplicate
            [200.0, 200.0, 280.0, 280.0]  # Distinct entity
        ]
        scores = [0.95, 0.88, 0.90]
        keep = non_max_suppression(boxes, scores, iou_threshold=0.40)
        self.assertEqual(len(keep), 2)
        self.assertIn(0, keep)
        self.assertIn(2, keep)


class TestKalmanFilter(unittest.TestCase):
    """Test 8-state Kalman Filter motion dynamics and convergence."""

    def test_kalman_constant_velocity_tracking(self):
        # Object starts at (100, 100) and moves with vx=5.0, vy=3.0 per frame
        w, h = 50.0, 50.0
        x, y = 100.0, 100.0
        vx, vy = 5.0, 3.0

        initial_box = [x, y, x + w, y + h]
        kf = KalmanBoxTracker(initial_box)

        # Simulate 15 time steps with linear motion
        for step in range(1, 16):
            x += vx
            y += vy
            measurement = [x, y, x + w, y + h]
            pred = kf.predict()
            kf.update(measurement)

        # Verify estimated velocity converges towards (vx, vy)
        du, dv, speed = kf.get_velocity()
        self.assertAlmostEqual(du, vx, delta=1.0)
        self.assertAlmostEqual(dv, vy, delta=1.0)
        self.assertAlmostEqual(speed, np.sqrt(vx**2 + vy**2), delta=1.5)


class TestTrackerLifecycleAndOcclusion(unittest.TestCase):
    """Test FSM lifecycle transitions, track association, and occlusion recovery."""

    def setUp(self):
        RealTimeMultiTracker.reset_id_counter()

    def test_fsm_confirmation_lifecycle(self):
        tracker = RealTimeMultiTracker(iou_threshold=0.30, min_hits=3, max_age=5)

        det = Detection(box=[100.0, 100.0, 160.0, 160.0], confidence=0.90, class_id=1, class_name="car")

        # Frame 1: Initial detection -> state is TENTATIVE
        active_1 = tracker.update([det])
        self.assertEqual(len(tracker.tracks), 1)
        self.assertEqual(tracker.tracks[0].state, TrackState.TENTATIVE)
        self.assertEqual(len(active_1), 0)  # Not confirmed yet!

        # Frame 2: Second hit -> still TENTATIVE
        active_2 = tracker.update([det])
        self.assertEqual(tracker.tracks[0].state, TrackState.TENTATIVE)
        self.assertEqual(len(active_2), 0)

        # Frame 3: Third hit -> transitions to CONFIRMED!
        active_3 = tracker.update([det])
        self.assertEqual(tracker.tracks[0].state, TrackState.CONFIRMED)
        self.assertEqual(len(active_3), 1)
        self.assertEqual(active_3[0].track_id, 1)

    def test_occlusion_recovery_preserves_id(self):
        """Verifies that an object occluded for multiple frames recovers the same Track ID upon re-emergence."""
        tracker = RealTimeMultiTracker(iou_threshold=0.25, min_hits=2, max_age=15)

        # Initial confirmed tracking
        box = [200.0, 200.0, 260.0, 260.0]
        det = Detection(box=box, confidence=0.95, class_id=1, class_name="vehicle")
        tracker.update([det])
        tracker.update([det])  # Confirmed as ID 1
        self.assertTrue(tracker.tracks[0].is_confirmed)
        original_id = tracker.tracks[0].track_id

        # Occlusion: Object disappears for 6 frames (e.g. behind pillar)
        for _ in range(6):
            tracker.update([])  # No detections
            self.assertEqual(tracker.tracks[0].state, TrackState.COASTING)

        # Object re-emerges near its predicted position
        reemerged_det = Detection(box=[205.0, 205.0, 265.0, 265.0], confidence=0.92, class_id=1, class_name="vehicle")
        active = tracker.update([reemerged_det])

        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].track_id, original_id, "Track ID must persist across occlusion!")
        self.assertTrue(active[0].is_confirmed)


class TestPreprocessor(unittest.TestCase):
    """Test aspect-ratio letterboxing and coordinate unpadding."""

    def test_letterbox_and_restore(self):
        # 16:9 widescreen frame 1920x1080
        dummy_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        target_size = (640, 640)

        letterboxed, ratio, (pad_w, pad_h) = Preprocessor.letterbox(dummy_frame, target_shape=target_size)
        self.assertEqual(letterboxed.shape, (640, 640, 3))

        # Check box mapping
        orig_box = [[300.0, 200.0, 800.0, 700.0]]
        # Manually project to letterbox space
        mapped_box = [
            orig_box[0][0] * ratio + pad_w,
            orig_box[0][1] * ratio + pad_h,
            orig_box[0][2] * ratio + pad_w,
            orig_box[0][3] * ratio + pad_h,
        ]

        restored = Preprocessor.restore_boxes([mapped_box], ratio, (pad_w, pad_h), orig_shape=(1080, 1920))
        self.assertAlmostEqual(restored[0][0], orig_box[0][0], delta=0.5)
        self.assertAlmostEqual(restored[0][1], orig_box[0][1], delta=0.5)
        self.assertAlmostEqual(restored[0][2], orig_box[0][2], delta=0.5)
        self.assertAlmostEqual(restored[0][3], orig_box[0][3], delta=0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
