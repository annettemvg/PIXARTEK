"""
Calibration module — two independent routines:

1. Perspective calibration (homography)
   The camera is mounted at eye-level (inclined, not top-down).
   We compute matrix H that maps the inclined view → top-down canvas plane.
   Triggered once per session via pixartek/vision/calibrate.

2. Color calibration
   Locks white-balance and exposure parameters by analyzing a known
   gray/white reference card captured at session start.
   Stored as per-channel scale factors applied to every subsequent frame.
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)

# ── State ─────────────────────────────────────────────────────────────────────
_H: np.ndarray | None = None          # 3×3 homography matrix
_color_scale = np.array([1.0, 1.0, 1.0])  # BGR scale factors


def is_calibrated() -> bool:
    return _H is not None


def get_homography() -> np.ndarray | None:
    return _H


def get_color_scale() -> np.ndarray:
    return _color_scale


# ── Perspective calibration ───────────────────────────────────────────────────

def calibrate_perspective(frame: np.ndarray, canvas_corners: list[list[float]] | None = None) -> bool:
    """
    Compute homography from frame.

    canvas_corners: [[x,y], ...] 4 points marking canvas corners in pixel space.
    If None, attempts automatic corner detection via ArUco markers or
    falls back to a centered bounding box estimate.
    """
    global _H
    h, w = frame.shape[:2]

    src_pts = _detect_corners(frame, canvas_corners, w, h)
    if src_pts is None:
        logger.warning("Corner detection failed — using identity homography")
        _H = np.eye(3, dtype=np.float64)
        return False

    # Destination: full rectified frame
    dst_pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]])

    try:
        import cv2
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        if H is None:
            logger.error("findHomography returned None")
            _H = np.eye(3, dtype=np.float64)
            return False
        _H = H
        inliers = int(mask.sum()) if mask is not None else 0
        logger.info(f"Homography computed — {inliers} inliers, det={np.linalg.det(H):.4f}")
        return True
    except ImportError:
        # cv2 not available — identity matrix (pass-through)
        _H = np.eye(3, dtype=np.float64)
        logger.warning("cv2 not available — homography set to identity")
        return True


def _detect_corners(frame: np.ndarray, manual: list | None, w: int, h: int) -> np.ndarray | None:
    """Try ArUco → manual → estimated bounding box."""
    # 1. Manual corners provided
    if manual and len(manual) == 4:
        return np.float32(manual)

    # 2. ArUco marker detection (RPi production)
    try:
        import cv2
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        params = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(aruco_dict, params)
        corners, ids, _ = detector.detectMarkers(gray)
        if ids is not None and len(ids) >= 4:
            # Sort markers by ID (0=TL, 1=TR, 2=BR, 3=BL)
            sorted_corners = [None] * 4
            for i, mid in enumerate(ids.flatten()):
                if mid < 4:
                    c = corners[i][0]
                    sorted_corners[mid] = c.mean(axis=0)
            if all(c is not None for c in sorted_corners):
                logger.info("ArUco markers detected for homography")
                return np.float32(sorted_corners)
    except Exception:
        pass

    # 3. Fallback: centered 80% bounding box estimate
    margin_x, margin_y = int(w * 0.1), int(h * 0.1)
    logger.info("Using estimated canvas corners (10% margin)")
    return np.float32([
        [margin_x,     margin_y    ],
        [w - margin_x, margin_y    ],
        [w - margin_x, h - margin_y],
        [margin_x,     h - margin_y],
    ])


# ── Color calibration ─────────────────────────────────────────────────────────

def calibrate_color(frame: np.ndarray) -> bool:
    """
    Analyze a gray/white reference card in the center of the frame.
    Compute per-channel scale factors to normalize the capture color space.
    """
    global _color_scale
    h, w = frame.shape[:2]

    # Sample center patch (10% of frame)
    y1, y2 = int(h * 0.45), int(h * 0.55)
    x1, x2 = int(w * 0.45), int(w * 0.55)
    patch = frame[y1:y2, x1:x2].astype(np.float32)

    means = patch.mean(axis=(0, 1))   # B, G, R means
    if means.min() < 1:
        logger.warning("Color calibration: patch too dark — keeping previous scale")
        return False

    # Target: neutral gray (equal channels)
    target = means.mean()
    _color_scale = target / means
    logger.info(f"Color calibrated — BGR scale: {_color_scale.round(3)}")
    return True


def apply_color(frame: np.ndarray) -> np.ndarray:
    """Apply color scale factors to a frame."""
    if np.allclose(_color_scale, 1.0):
        return frame
    corrected = frame.astype(np.float32) * _color_scale
    return np.clip(corrected, 0, 255).astype(np.uint8)


def apply_homography(frame: np.ndarray) -> np.ndarray:
    """Warp frame using computed homography."""
    if _H is None or np.allclose(_H, np.eye(3)):
        return frame
    try:
        import cv2
        h, w = frame.shape[:2]
        return cv2.warpPerspective(frame, _H, (w, h))
    except ImportError:
        return frame
