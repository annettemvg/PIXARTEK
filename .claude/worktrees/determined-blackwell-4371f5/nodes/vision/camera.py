"""
Camera abstraction for the vision node.

  RPi (production):  Picamera2 — libcamera stack, CSI ribbon HD camera
  Dev (macOS/Linux): cv2.VideoCapture — webcam or USB camera
  Dev (headless):    synthetic frames generated from numpy
"""
import logging
import numpy as np

from config import DEV_MODE, CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT

logger = logging.getLogger(__name__)

_cap        = None   # cv2 VideoCapture
_picamera   = None   # Picamera2 instance
_use_mock   = False  # True when no real camera available


# ── Public API ────────────────────────────────────────────────────────────────

def init() -> bool:
    """Open camera. Returns True on success."""
    global _cap, _picamera, _use_mock

    # 1. Try Picamera2 (CSI ribbon camera)
    if _init_picamera():
        return True

    # 2. Try cv2 USB camera (Logitech, etc.)
    try:
        import cv2
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            _cap = cap
            logger.info(f"cv2 USB camera {CAMERA_INDEX} opened ({FRAME_WIDTH}×{FRAME_HEIGHT})")
            return True
        cap.release()
    except ImportError:
        pass

    # 3. Fallback: synthetic frames
    logger.warning("No camera available — using synthetic frames")
    _use_mock = True
    return True


def read() -> np.ndarray | None:
    """
    Capture one frame as BGR numpy array (H×W×3).
    Returns None on failure.
    """
    if _use_mock:
        return _synthetic_frame()

    if _picamera:
        return _read_picamera()

    if _cap:
        try:
            import cv2
            ok, frame = _cap.read()
            return frame if ok else None
        except Exception as e:
            logger.error(f"cv2 read error: {e}")
            return None

    return None


def release():
    """Release camera resources."""
    global _cap, _picamera
    if _cap:
        try:
            _cap.release()
        except Exception:
            pass
        _cap = None

    if _picamera:
        try:
            _picamera.stop()
            _picamera.close()
        except Exception:
            pass
        _picamera = None


# ── Picamera2 (RPi) ───────────────────────────────────────────────────────────

def _init_picamera() -> bool:
    global _picamera
    try:
        from picamera2 import Picamera2
        pc = Picamera2()
        cfg = pc.create_still_configuration(
            main={"size": (FRAME_WIDTH, FRAME_HEIGHT), "format": "BGR888"}
        )
        pc.configure(cfg)
        pc.start()
        _picamera = pc
        logger.info(f"Picamera2 started ({FRAME_WIDTH}×{FRAME_HEIGHT})")
        return True
    except Exception as e:
        logger.error(f"Picamera2 init failed: {e}")
        return False


def _read_picamera() -> np.ndarray | None:
    try:
        return _picamera.capture_array("main")
    except Exception as e:
        logger.error(f"Picamera2 capture error: {e}")
        return None


# ── Synthetic frames (headless dev) ──────────────────────────────────────────

_frame_counter = 0

def _synthetic_frame() -> np.ndarray:
    """
    Returns a BGR frame that slowly changes color —
    simulates a canvas being painted over time.
    """
    global _frame_counter
    _frame_counter += 1

    h, w = FRAME_HEIGHT, FRAME_WIDTH
    frame = np.zeros((h, w, 3), dtype=np.uint8)

    # Slowly shifting background color
    t = _frame_counter * 0.03
    r = int(127 + 60 * np.sin(t))
    g = int(100 + 40 * np.sin(t + 1.5))
    b = int(80  + 50 * np.sin(t + 3.0))
    frame[:] = (b, g, r)   # BGR

    # Simulate a painted stroke zone (random noise patch)
    patch = frame[h//3:2*h//3, w//3:2*w//3]
    ph, pw = patch.shape[:2]
    rng = np.random.default_rng(seed=_frame_counter // 10)
    noise = rng.integers(0, 40, (ph, pw, 3), dtype=np.uint8)
    frame[h//3:2*h//3, w//3:2*w//3] = np.clip(
        patch.astype(int) + noise - 20, 0, 255
    ).astype(np.uint8)

    return frame
