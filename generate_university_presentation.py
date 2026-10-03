"""PowerPoint Generator strictly styled to match the Marwadi University reference presentation format.

Key Reference Design Features:
- Teal / Cyan top gradient/solid background (#5FAAB7)
- Large rounded-corner white card container filling the slide body
- Slide title on top-left in bold dark charcoal/black
- University/Department logo badge on top-right
- Section subheadings in bright blue (#0070C0)
- Primary bullet points (•) with key phrases highlighted in blue/red
- Distinct checkmarks (✔) and square bullets (❑)
- Page numbers in the bottom-right corner of the white card
- Dedicated Title slide, Contents slide, Content slides, and centered 'Thank you!!' closing slide
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_university_styled_deck(output_filename="RealTime_Object_Recognition_and_Tracking_University_Format.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Reference Color Palette
    HEADER_TEAL = RGBColor(95, 170, 183)      # Teal/Cyan top band (#5FAAB7)
    WHITE_CARD = RGBColor(255, 255, 255)       # Slide body white rounded card
    TEXT_BLACK = RGBColor(25, 30, 40)         # Primary slide text
    TITLE_BLACK = RGBColor(15, 20, 30)        # Slide title text
    SUBHEAD_BLUE = RGBColor(0, 112, 192)      # Section blue headers (#0070C0)
    KEYWORD_BLUE = RGBColor(0, 112, 192)      # Highlighted blue keywords
    KEYWORD_RED = RGBColor(220, 50, 50)       # Highlighted red keywords
    PAGE_NUM_GRAY = RGBColor(70, 80, 95)      # Page number color
    CARD_BORDER = RGBColor(215, 225, 230)     # Subtle card border

    def apply_base_template(slide, title_text, page_num):
        # 1. Outer Slide Background (Teal)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = HEADER_TEAL
        bg.line.fill.background()

        # 2. Slide Title (Top Left)
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(8.8), Inches(0.85))
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = TITLE_BLACK

        # 3. Top-Right Logo Badge (Matching Reference Header Logo)
        logo_rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.8), Inches(0.18), Inches(0.65), Inches(0.65))
        logo_rect.fill.solid()
        logo_rect.fill.fore_color.rgb = RGBColor(0, 160, 190)
        logo_rect.line.color.rgb = RGBColor(255, 255, 255)
        logo_rect.line.width = Pt(1.5)
        tf_l = logo_rect.text_frame
        p_l = tf_l.paragraphs[0]
        p_l.text = "M"
        p_l.font.size = Pt(22)
        p_l.font.bold = True
        p_l.font.color.rgb = RGBColor(255, 255, 255)
        p_l.alignment = PP_ALIGN.CENTER

        logo_text = slide.shapes.add_textbox(Inches(10.5), Inches(0.12), Inches(2.5), Inches(0.75))
        tf_lt = logo_text.text_frame
        p_lt1 = tf_lt.paragraphs[0]
        p_lt1.text = "Marwadi"
        p_lt1.font.size = Pt(16)
        p_lt1.font.bold = True
        p_lt1.font.color.rgb = RGBColor(30, 40, 50)
        p_lt2 = tf_lt.add_paragraph()
        p_lt2.text = "University"
        p_lt2.font.size = Pt(12)
        p_lt2.font.bold = True
        p_lt2.font.color.rgb = RGBColor(40, 60, 70)
        p_lt3 = tf_lt.add_paragraph()
        p_lt3.text = "Faculty of Computer Engineering"
        p_lt3.font.size = Pt(8)
        p_lt3.font.color.rgb = RGBColor(70, 90, 100)

        # 4. White Rounded Card Body
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.25), Inches(1.15), Inches(12.833), Inches(6.1))
        card.fill.solid()
        card.fill.fore_color.rgb = WHITE_CARD
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1)

        # 5. Page Number in Bottom-Right Corner
        pg_box = slide.shapes.add_textbox(Inches(12.2), Inches(6.7), Inches(0.7), Inches(0.4))
        tf_pg = pg_box.text_frame
        p_pg = tf_pg.paragraphs[0]
        p_pg.text = str(page_num)
        p_pg.font.size = Pt(14)
        p_pg.font.bold = True
        p_pg.font.color.rgb = PAGE_NUM_GRAY
        p_pg.alignment = PP_ALIGN.RIGHT

        # Return a content text box inside the white card
        content_box = slide.shapes.add_textbox(Inches(0.6), Inches(1.35), Inches(12.1), Inches(5.3))
        tf_c = content_box.text_frame
        tf_c.word_wrap = True
        return tf_c

    # =========================================================================
    # SLIDE 1: Title Slide (Matching Reference Page 1)
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = WHITE_CARD
    bg1.line.fill.background()

    # Top-Right University Logo on white canvas
    logo_rect1 = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.5), Inches(0.3), Inches(0.75), Inches(0.75))
    logo_rect1.fill.solid()
    logo_rect1.fill.fore_color.rgb = RGBColor(0, 160, 190)
    logo_rect1.line.color.rgb = WHITE_CARD
    p_lr1 = logo_rect1.text_frame.paragraphs[0]
    p_lr1.text = "M"
    p_lr1.font.size = Pt(26)
    p_lr1.font.bold = True
    p_lr1.font.color.rgb = WHITE_CARD
    p_lr1.alignment = PP_ALIGN.CENTER

    logo_tb1 = slide1.shapes.add_textbox(Inches(10.35), Inches(0.25), Inches(2.6), Inches(0.9))
    p_lt1 = logo_tb1.text_frame.paragraphs[0]
    p_lt1.text = "Marwadi"
    p_lt1.font.size = Pt(18)
    p_lt1.font.bold = True
    p_lt1.font.color.rgb = RGBColor(30, 40, 50)
    p_lt2 = logo_tb1.text_frame.add_paragraph()
    p_lt2.text = "University"
    p_lt2.font.size = Pt(14)
    p_lt2.font.bold = True
    p_lt2.font.color.rgb = RGBColor(50, 70, 80)
    p_lt3 = logo_tb1.text_frame.add_paragraph()
    p_lt3.text = "Department of CSE - AI, ML & DS"
    p_lt3.font.size = Pt(9)
    p_lt3.font.color.rgb = RGBColor(90, 110, 120)

    # Left-hand Content Info
    title_tb = slide1.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(6.5), Inches(6.0))
    tf1 = title_tb.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "01AI0510 - Computer Vision & Deep Learning"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = TITLE_BLACK
    p.space_after = Pt(24)

    p = tf1.add_paragraph()
    p.text = "Capstone Project Presentation"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(8)

    p = tf1.add_paragraph()
    p.text = "Real-Time Object Recognition\nand Multi-Object Tracking\nin Video Streams"
    p.font.size = Pt(26)
    p.font.bold = True
    p.font.color.rgb = TITLE_BLACK
    p.space_after = Pt(28)

    p = tf1.add_paragraph()
    p.text = "Prepared by:"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = TITLE_BLACK

    p = tf1.add_paragraph()
    p.text = "Bajaru Dinesh Goud"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE

    p = tf1.add_paragraph()
    p.text = "Department of CSE - AI, ML & DS"
    p.font.size = Pt(14)
    p.font.color.rgb = TEXT_BLACK

    # Right-hand side Thematic Word Cloud / Graphic Block (Matching Page 1 of Reference)
    cloud_tb = slide1.shapes.add_textbox(Inches(7.2), Inches(1.5), Inches(5.5), Inches(5.0))
    tfc = cloud_tb.text_frame
    tfc.word_wrap = True

    cloud_lines = [
        ("COMPUTER VISION", Pt(34), RGBColor(220, 50, 50), True),
        ("REAL-TIME RECOGNITION", Pt(28), RGBColor(0, 112, 192), True),
        ("KALMAN FILTER", Pt(32), RGBColor(240, 120, 20), True),
        ("BIPARTITE MATCHING", Pt(22), RGBColor(40, 160, 100), True),
        ("SORT PARADIGM   •   DEEP LEARNING", Pt(16), RGBColor(120, 60, 180), True),
        ("OCCLUSION RECOVERY   •   TRAJECTORIES", Pt(16), RGBColor(0, 150, 200), True),
        ("OPENCV   •   YOLO   •   PYTHON PIPELINE", Pt(17), RGBColor(70, 80, 90), True),
    ]
    for i, (txt, sz, clr, bld) in enumerate(cloud_lines):
        p = tfc.paragraphs[0] if i == 0 else tfc.add_paragraph()
        p.text = txt
        p.font.size = sz
        p.font.bold = bld
        p.font.color.rgb = clr
        p.alignment = PP_ALIGN.CENTER
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 2: Contents (Matching Reference Page 2)
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    tf2 = apply_base_template(slide2, "Contents", 2)

    contents = [
        "Introduction & Real-Time Computer Vision Challenges",
        "End-to-End System Pipeline Overview",
        "Video Ingestion & Threaded Capture Buffering",
        "Aspect-Ratio Preserving Preprocessing (Letterboxing)",
        "Object Recognition & Localization (YOLO / OpenCV)",
        "State Estimation using 8-State Linear Kalman Filter",
        "Bipartite Data Association (Hungarian Algorithm)",
        "Track Lifecycle Management & Occlusion Recovery",
        "Motion Trajectory Analytics & Telemetry HUD Overlay",
        "Automated Verification & Synthetic Stream Benchmarks",
        "Practical Applications, System Extensibility & Conclusion"
    ]
    for i, item in enumerate(contents):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.text = f"❑  {item}"
        p.font.size = Pt(15)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(7)

    # =========================================================================
    # SLIDE 3: Introduction & Problem Statement
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    tf3 = apply_base_template(slide3, "Introduction & Problem Statement", 3)

    p = tf3.paragraphs[0]
    p.text = "Overview of Real-Time Vision & Tracking"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    p = tf3.add_paragraph()
    p.text = "• In computer vision, detecting objects within single isolated frames is only the first step. To understand dynamics, automated systems must recognize objects and track their movements persistently over time."
    p.font.size = Pt(15)
    p.font.color.rgb = TEXT_BLACK
    p.space_after = Pt(10)

    p = tf3.add_paragraph()
    p.text = "• Standard video processing architectures encounter three critical bottlenecks:"
    p.font.size = Pt(15)
    p.font.color.rgb = TEXT_BLACK
    p.space_after = Pt(8)

    p = tf3.add_paragraph()
    p.text = "✔ Hardware Buffer Lag: Camera drivers buffer frames synchronously, leading to progressive multi-second latency drift in live video streams."
    p.font.size = Pt(14)
    p.font.color.rgb = TEXT_BLACK
    p.space_after = Pt(6)

    p = tf3.add_paragraph()
    p.text = "✔ Spatial Deformation: Naive image resizing causes aspect ratio distortion, degrading detector feature representation."
    p.font.size = Pt(14)
    p.font.color.rgb = TEXT_BLACK
    p.space_after = Pt(6)

    p = tf3.add_paragraph()
    p.text = "✔ Identity Switching & Occlusion: Moving objects crossing paths or passing behind obstacles frequently lose their identity."
    p.font.size = Pt(14)
    p.font.color.rgb = TEXT_BLACK

    # =========================================================================
    # SLIDE 4: The 6-Stage Computer Vision Pipeline
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    tf4 = apply_base_template(slide4, "Computer Vision Pipeline Architecture", 4)

    p = tf4.paragraphs[0]
    p.text = "The 6 Core Pipeline Stages"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    p = tf4.add_paragraph()
    p.text = "• The system coordinates six tightly decoupled phases to guarantee real-time throughput:"
    p.font.size = Pt(15)
    p.font.color.rgb = TEXT_BLACK
    p.space_after = Pt(10)

    phases = [
        "Phase 1: Video Ingestion — Thread-safe asynchronous capture buffer to eliminate driver queuing latency.",
        "Phase 2: Preprocessing — Aspect-ratio letterboxing, normalization, and tensor shaping.",
        "Phase 3: Object Recognition — Deep feature extraction, class whitelisting, and CIoU Non-Maximum Suppression.",
        "Phase 4: State Estimation & Tracking — 8-state Kalman Filter motion modeling and Hungarian bipartite association.",
        "Phase 5: Trajectory Analytics — Centroid history deques, progressive fading comet trails, and velocity vectors.",
        "Phase 6: Visual Telemetry Overlay — Live FPS dashboard, latency monitoring, and video recording."
    ]
    for ph in phases:
        p = tf4.add_paragraph()
        p.text = f"✔  {ph}"
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(7)

    # =========================================================================
    # SLIDE 5: Video Ingestion & Asynchronous Decoupling
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    tf5 = apply_base_template(slide5, "Phase 1: Stream Ingestion & Decoupling", 5)

    p = tf5.paragraphs[0]
    p.text = "Decoupled Frame Acquisition"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    p = tf5.add_paragraph()
    p.text = "• The VideoStreamHandler implements an asynchronous worker thread that isolates frame capture from neural network inference."
    p.font.size = Pt(15)
    p.font.color.rgb = TEXT_BLACK
    p.space_after = Pt(8)

    points5 = [
        "Synchronous cv2.VideoCapture reads from an internal driver ring-buffer; if inference takes 30ms, the stream falls behind real-time.",
        "Our threaded worker polls the hardware at full sensor framerate and maintains only the latest frame in an atomic locked buffer.",
        "Old, unconsumed buffer frames are automatically discarded to guarantee true zero-lag processing.",
        "Supports webcams, high-resolution local video files (.mp4/.avi), and low-latency RTSP IP security streams."
    ]
    for pt in points5:
        p = tf5.add_paragraph()
        p.text = f"✔  {pt}"
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 6: Preprocessing & Aspect-Ratio Letterboxing
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    tf6 = apply_base_template(slide6, "Phase 2: Image Preprocessing", 6)

    p = tf6.paragraphs[0]
    p.text = "Aspect-Ratio Preserving Letterbox Resizing"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    p = tf6.add_paragraph()
    p.text = "• Directly resizing arbitrary aspect ratios (e.g. 16:9 or 4:3) to a square 640x640 model input squashes visual features."
    p.font.size = Pt(15)
    p.font.color.rgb = TEXT_BLACK
    p.space_after = Pt(8)

    points6 = [
        "Uniform Scale Factor: r = min(W_target / W_orig, H_target / H_orig).",
        "Symmetric Padding: Computes margin dw = (W_target - W_unpad) / 2 and dh = (H_target - H_unpad) / 2.",
        "Border Extension: Fills padding with neutral gray (114, 114, 114) preserving aspect ratio fidelity.",
        "Color Space Normalization: Converts BGR to RGB and scales uint8 values [0, 255] to float32 [0.0, 1.0].",
        "Inverse Coordinate Projection: Detected bounding boxes [x'1, y'1, x'2, y'2] are restored to original resolution via xi = (x'i - dw) / r."
    ]
    for pt in points6:
        p = tf6.add_paragraph()
        p.text = f"✔  {pt}"
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(7)

    # =========================================================================
    # SLIDE 7: Deep Object Detection & Localization
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    tf7 = apply_base_template(slide7, "Phase 3: Object Recognition & Localization", 7)

    p = tf7.paragraphs[0]
    p.text = "Deep Neural Detection & Multi-Scale Feature Maps"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    points7 = [
        "Multi-Scale Feature Pyramids: Features extracted across strides P3 (stride 8 for small objects), P4 (stride 16), and P5 (stride 32 for large objects).",
        "Anchor-Free Decoupled Head: Predicts object classification probabilities and bounding box regression parameters independently.",
        "Complete IoU (CIoU) Loss: Penalizes bounding box overlap, center-point Euclidean distance, and aspect ratio discrepancies.",
        "Multi-Backend Architecture: Supports YOLOv8/11 deep learning inference and high-speed OpenCV classical motion fallback."
    ]
    for pt in points7:
        p = tf7.add_paragraph()
        p.text = f"•  {pt}"
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 8: Class Filtering & Non-Maximum Suppression (NMS)
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    tf8 = apply_base_template(slide8, "Phase 3: Whitelisting & NMS Filtering", 8)

    p = tf8.paragraphs[0]
    p.text = "Filtering and Redundancy Elimination"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    points8 = [
        "Target Class Whitelisting: Configurable whitelist allows user to isolate specific objects (e.g., person, car, laptop, bottle), discarding unneeded classes before tracking.",
        "Confidence Thresholding: Prunes low-confidence background candidates below configurable threshold (default 0.40).",
        "Non-Maximum Suppression (NMS): Adjacent grid cells frequently generate multiple overlapping bounding boxes for a single entity.",
        "Intersection over Union (IoU) Suppression: Evaluates IoU across candidate boxes and discards boxes exceeding NMS threshold (default 0.45):",
        "   Formula: IoU(Box_A, Box_B) = Area(Box_A ∩ Box_B) / Area(Box_A ∪ Box_B)"
    ]
    for pt in points8:
        p = tf8.add_paragraph()
        p.text = f"✔  {pt}"
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(7)

    # =========================================================================
    # SLIDE 9: Kalman Filter State Estimation
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    tf9 = apply_base_template(slide9, "Phase 4: State Estimation (Kalman Filter)", 9)

    p = tf9.paragraphs[0]
    p.text = "8-Dimensional Motion State Space"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    p = tf9.add_paragraph()
    p.text = "• Each tracked object is modeled in continuous 2D space using an 8-element state vector representing position and velocity:"
    p.font.size = Pt(15)
    p.font.color.rgb = TEXT_BLACK
    p.space_after = Pt(8)

    points9 = [
        "State Vector: x = [ u,  v,  s,  r,  du,  dv,  ds,  dr ]^T",
        "u, v : Horizontal and vertical pixel coordinates of bounding box center.",
        "s : Scale (bounding box area = width * height).",
        "r : Aspect ratio (width / height).",
        "du, dv, ds, dr : Respective instantaneous velocities (pixels / frame).",
        "Transition Matrix (F) : Models constant velocity linear motion where x_{t+1} = x_t + v_t * dt.",
        "Measurement Matrix (H) : Extracts directly observable parameters [ u, v, s, r ]."
    ]
    for pt in points9:
        p = tf9.add_paragraph()
        p.text = f"•  {pt}"
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(6)

    # =========================================================================
    # SLIDE 10: Kalman Predict & Update Formulation
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    tf10 = apply_base_template(slide10, "Phase 4: Kalman Predict & Update Cycle", 10)

    p = tf10.paragraphs[0]
    p.text = "Mathematical Formulation of the Filter Cycle"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(8)

    formulas = [
        "1. Prediction Phase (A Priori State Estimate):",
        "   • State Prediction: x̂_{k|k-1} = F * x̂_{k-1|k-1}",
        "   • Error Covariance Prediction: P_{k|k-1} = F * P_{k-1|k-1} * F^T + Q",
        "2. Innovation / Measurement Residual:",
        "   • Residual: y_k = z_k - H * x̂_{k|k-1}",
        "   • Residual Covariance: S_k = H * P_{k|k-1} * H^T + R",
        "3. Optimal Correction Phase (A Posteriori State Estimate):",
        "   • Optimal Kalman Gain: K_k = P_{k|k-1} * H^T * inv(S_k)",
        "   • Updated State Estimate: x̂_{k|k} = x̂_{k|k-1} + K_k * y_k",
        "   • Updated Covariance Estimate: P_{k|k} = (I - K_k * H) * P_{k|k-1}"
    ]
    for fm in formulas:
        p = tf10.add_paragraph()
        p.text = fm
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(3)

    # =========================================================================
    # SLIDE 11: Bipartite Association (Hungarian Algorithm)
    # =========================================================================
    slide11 = prs.slides.add_slide(blank_layout)
    tf11 = apply_base_template(slide11, "Phase 4: Bipartite Data Association", 11)

    p = tf11.paragraphs[0]
    p.text = "Cost Matrix & Hungarian Assignment (SORT Paradigm)"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    points11 = [
        "IoU Cost Matrix: Computes pairwise overlap between M current detections and N predicted tracks: Cost(i, j) = 1 - IoU(Det_i, Track_j).",
        "Global Optimization: The Hungarian (Munkres) / linear sum assignment algorithm solves the bipartite matching problem in polynomial time O(N^3).",
        "IoU Gating: Matches with IoU below threshold (0.30) are rejected to prevent incorrect cross-class associations.",
        "Three Assignment Outcomes:",
        "   1. Matched Pairs: Existing track updated with matched measurement.",
        "   2. Unmatched Detections: New candidate objects entering the field of view.",
        "   3. Unmatched Tracks: Existing objects occluded or temporarily missed."
    ]
    for pt in points11:
        p = tf11.add_paragraph()
        p.text = f"✔  {pt}"
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(6)

    # =========================================================================
    # SLIDE 12: Track Lifecycle & Occlusion Recovery
    # =========================================================================
    slide12 = prs.slides.add_slide(blank_layout)
    tf12 = apply_base_template(slide12, "Phase 4: Track Lifecycle Management", 12)

    p = tf12.paragraphs[0]
    p.text = "Finite State Machine for Object Persistence"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    lifecycles = [
        "TENTATIVE State: Initialized upon new unmatched detection. Must be detected in min_hits (3) consecutive frames to filter false positives.",
        "CONFIRMED State: Actively sustained track. Rendered to display with persistent Track ID and trajectory history.",
        "LOST / COASTING State: If an object is temporarily occluded (e.g., walking behind a pillar or vehicle), the Kalman filter predicts forward trajectory without measurements for up to max_age (30 frames).",
        "OCCLUSION RECOVERY: When the object re-emerges, bipartite matching re-associates it to the same original Track ID.",
        "DELETED State: Pruned from memory if the object remains lost longer than max_age."
    ]
    for lc in lifecycles:
        p = tf12.add_paragraph()
        p.text = f"•  {lc}"
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 13: Motion Trajectory Analytics
    # =========================================================================
    slide13 = prs.slides.add_slide(blank_layout)
    tf13 = apply_base_template(slide13, "Phase 5: Motion Trajectory Analytics", 13)

    p = tf13.paragraphs[0]
    p.text = "Dynamic Breadcrumb Trails & Velocity Vectors"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    points13 = [
        "Centroid History Queue: Each active track stores historical center coordinates in a bounded FIFO deque (default length 40).",
        "Progressive Fading Comet Tails: Historical polylines are rendered with linear thickness and transparency decay: thickness(i) = max(1, 3 * (i / N_trail)).",
        "Sub-Pixel Velocity Estimation: Filtered velocity derivatives (du, dv) from the Kalman state space yield instantaneous speed: Speed = sqrt(du^2 + dv^2).",
        "Directional Heading Arrows: Dynamic velocity vector arrows projected from the centroid indicate trajectory heading in real time."
    ]
    for pt in points13:
        p = tf13.add_paragraph()
        p.text = f"✔  {pt}"
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 14: Visualizer & Telemetry HUD Overlay
    # =========================================================================
    slide14 = prs.slides.add_slide(blank_layout)
    tf14 = apply_base_template(slide14, "Phase 6: Visualizer & Telemetry HUD", 14)

    p = tf14.paragraphs[0]
    p.text = "HUD Dashboard & User Controls"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    points14 = [
        "Semi-Transparent Telemetry Banner: Overlays real-time FPS, active track count, detection latency (ms), and tracking latency (ms).",
        "Golden-Ratio Color Hashing: Assigns 100 visually distinct, repeatable BGR colors based on Track ID: h_k = (0.1 + k * 0.618) mod 1.0.",
        "Corner-Bracket Bounding Boxes: High-contrast bounding boxes with corner accents and filled label badges (#ID: ClassName Score%).",
        "Interactive Hotkeys: [q] Clean Exit, [p/SPACE] Pause/Resume, [t] Toggle Trails, [b] Toggle Boxes, [s] Save Snapshot Image."
    ]
    for pt in points14:
        p = tf14.add_paragraph()
        p.text = f"•  {pt}"
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 15: Experimental Verification & Benchmarks
    # =========================================================================
    slide15 = prs.slides.add_slide(blank_layout)
    tf15 = apply_base_template(slide15, "Experimental Verification & Results", 15)

    p = tf15.paragraphs[0]
    p.text = "Empirical Validation & Benchmark Summary"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    bench_points = [
        "Automated Synthetic Stream: Evaluated on 120 synthetic video frames featuring 3 crossing targets and obstacle occlusion.",
        "Processing Throughput: Achieved 100.2 FPS sustained real-time speed on CPU.",
        "Component Latencies: Detection average 5.7 ms | Tracking average 1.1 ms.",
        "Algorithmic Unit Tests: 100% pass on bounding box conversions, Kalman velocity estimation, IoU calculations, and Hungarian matching.",
        "Occlusion Handling: Targets passing behind obstacle pillar maintained identical Track IDs upon re-emergence."
    ]
    for bp in bench_points:
        p = tf15.add_paragraph()
        p.text = f"✔  {bp}"
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(6)

    # Add snapshot image if available
    snap_path = "synthetic_snapshot.jpg"
    if os.path.exists(snap_path):
        slide15.shapes.add_picture(snap_path, Inches(7.5), Inches(2.2), Inches(5.3), Inches(4.2))

    # =========================================================================
    # SLIDE 16: Practical Applications & Extensibility
    # =========================================================================
    slide16 = prs.slides.add_slide(blank_layout)
    tf16 = apply_base_template(slide16, "Real-World Applications & Future Scope", 16)

    p = tf16.paragraphs[0]
    p.text = "Industry Applications & Architectural Extensions"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = SUBHEAD_BLUE
    p.space_after = Pt(10)

    points16 = [
        "Autonomous Vehicles & ADAS: Pedestrian trajectory prediction, cyclist collision avoidance, and lane-level traffic monitoring.",
        "Intelligent Video Analytics (IVA): Security perimeter protection, unauthorized intrusion detection, and loitering analysis.",
        "Retail Foot-Traffic Analytics: Customer navigation heatmaps, queue dwell times, and checkout efficiency.",
        "Sports Analytics: Player movement tracking, team formation analysis, and instantaneous sprint velocity profiling.",
        "Deep Appearance Features (DeepSORT): Extensible to include Re-ID deep CNN feature embeddings in cost matrix for long-term re-identification.",
        "Edge Deployment: Exportable to ONNX, TensorRT, and OpenVINO for embedded Jetson and edge devices."
    ]
    for pt in points16:
        p = tf16.add_paragraph()
        p.text = f"•  {pt}"
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_BLACK
        p.space_after = Pt(7)

    # =========================================================================
    # SLIDE 17: Thank You Slide (Matching Reference Page 60)
    # =========================================================================
    slide17 = prs.slides.add_slide(blank_layout)
    # Base Teal Background
    bg17 = slide17.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg17.fill.solid()
    bg17.fill.fore_color.rgb = HEADER_TEAL
    bg17.line.fill.background()

    # White Rounded Card Body
    card17 = slide17.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.25), Inches(1.15), Inches(12.833), Inches(6.1))
    card17.fill.solid()
    card17.fill.fore_color.rgb = WHITE_CARD
    card17.line.color.rgb = CARD_BORDER
    card17.line.width = Pt(1)

    # Top-Right University Logo
    logo_rect17 = slide17.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.8), Inches(0.18), Inches(0.65), Inches(0.65))
    logo_rect17.fill.solid()
    logo_rect17.fill.fore_color.rgb = RGBColor(0, 160, 190)
    logo_rect17.line.color.rgb = RGBColor(255, 255, 255)
    logo_rect17.line.width = Pt(1.5)
    p_l17 = logo_rect17.text_frame.paragraphs[0]
    p_l17.text = "M"
    p_l17.font.size = Pt(22)
    p_l17.font.bold = True
    p_l17.font.color.rgb = RGBColor(255, 255, 255)
    p_l17.alignment = PP_ALIGN.CENTER

    logo_text17 = slide17.shapes.add_textbox(Inches(10.5), Inches(0.12), Inches(2.5), Inches(0.75))
    p_lt17 = logo_text17.text_frame.paragraphs[0]
    p_lt17.text = "Marwadi"
    p_lt17.font.size = Pt(16)
    p_lt17.font.bold = True
    p_lt17.font.color.rgb = RGBColor(30, 40, 50)
    p_lt27 = logo_text17.text_frame.add_paragraph()
    p_lt27.text = "University"
    p_lt27.font.size = Pt(12)
    p_lt27.font.bold = True
    p_lt27.font.color.rgb = RGBColor(40, 60, 70)

    # Centered "Thank you!!" text (matching reference page 60)
    ty_box = slide17.shapes.add_textbox(Inches(2.0), Inches(3.2), Inches(9.333), Inches(2.0))
    tf_ty = ty_box.text_frame
    p_ty = tf_ty.paragraphs[0]
    p_ty.text = "Thank you!!"
    p_ty.font.size = Pt(56)
    p_ty.font.bold = True
    p_ty.font.color.rgb = TITLE_BLACK
    p_ty.alignment = PP_ALIGN.CENTER

    # Page number 17
    pg17 = slide17.shapes.add_textbox(Inches(12.2), Inches(6.7), Inches(0.7), Inches(0.4))
    p_pg17 = pg17.text_frame.paragraphs[0]
    p_pg17.text = "17"
    p_pg17.font.size = Pt(14)
    p_pg17.font.bold = True
    p_pg17.font.color.rgb = PAGE_NUM_GRAY
    p_pg17.alignment = PP_ALIGN.RIGHT

    # Save presentation
    prs.save(output_filename)
    print(f"[Success] University format presentation generated: {output_filename}")

if __name__ == "__main__":
    create_university_styled_deck()
