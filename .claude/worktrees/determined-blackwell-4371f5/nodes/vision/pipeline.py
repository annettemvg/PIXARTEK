"""
Vision analysis pipeline — runs per frame against a reference image.

Steps:
  1. Color correction + perspective warp
  2. Canvas ROI crop
  3. Resize canvas to reference dimensions
  4. Pixel difference (absdiff) → overall precision %
  5. Color histogram comparison → delta-E approximation
  6. Canny edge detection → stroke error zones
  7. Returns structured FeedbackResult
"""
import logging
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path

import calibration
from config import CANVAS_ROI, FRAME_WIDTH, FRAME_HEIGHT

logger = logging.getLogger(__name__)


@dataclass
class StrokeError:
    zone: str
    message: str


@dataclass
class FeedbackResult:
    precision_pct: float
    color_deviation: float          # delta-E approximation (lower = better)
    stroke_errors: list[StrokeError] = field(default_factory=list)
    suggestions: list[str]          = field(default_factory=list)


# Current reference image (BGR numpy array, resized to analysis resolution)
_reference: np.ndarray | None = None
_reference_id: str = ""
_reference_stage: int = 0

ANALYSIS_W, ANALYSIS_H = 320, 240   # resize target for fast processing


def set_reference(image_path: str, artwork_id: str, stage: int) -> bool:
    """Load a reference image for the current stage."""
    global _reference, _reference_id, _reference_stage
    try:
        path = Path(image_path)
        if not path.exists():
            logger.error(f"Reference not found: {image_path}")
            return False

        try:
            import cv2
            img = cv2.imread(str(path))
            if img is None:
                raise ValueError("cv2.imread returned None")
            img = cv2.resize(img, (ANALYSIS_W, ANALYSIS_H))
        except ImportError:
            # No cv2 — use Pillow
            from PIL import Image
            pil = Image.open(path).convert("RGB").resize((ANALYSIS_W, ANALYSIS_H))
            img = np.array(pil)[:, :, ::-1]  # RGB→BGR

        _reference = img
        _reference_id = artwork_id
        _reference_stage = stage
        logger.info(f"Reference set: {image_path} ({artwork_id} stage {stage})")
        return True
    except Exception as e:
        logger.error(f"set_reference error: {e}")
        return False


def analyze(frame: np.ndarray) -> FeedbackResult | None:
    """
    Run full pipeline on a captured frame.
    Returns None if no reference is loaded or cv2/numpy unavailable.
    """
    if _reference is None:
        return None

    try:
        # 1. Color + perspective correction
        corrected = calibration.apply_color(frame)
        warped    = calibration.apply_homography(corrected)

        # 2. Canvas ROI crop
        canvas = _crop_roi(warped)

        # 3. Resize to analysis resolution
        try:
            import cv2
            canvas_small = cv2.resize(canvas, (ANALYSIS_W, ANALYSIS_H))
        except ImportError:
            canvas_small = _resize_numpy(canvas, ANALYSIS_W, ANALYSIS_H)

        # 4. Pixel difference → precision
        diff = np.abs(canvas_small.astype(np.int16) - _reference.astype(np.int16))
        mean_diff = float(diff.mean())
        precision = max(0.0, min(100.0, 100.0 - (mean_diff / 255.0) * 100.0))

        # 5. Color deviation (per-channel histogram distance)
        color_dev = _histogram_deviation(canvas_small, _reference)

        # 6. Stroke error zones
        errors = _detect_stroke_errors(canvas_small, _reference)

        # 7. Suggestions
        suggestions = _build_suggestions(precision, color_dev, errors)

        return FeedbackResult(
            precision_pct=round(precision, 1),
            color_deviation=round(color_dev, 2),
            stroke_errors=errors,
            suggestions=suggestions,
        )

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _crop_roi(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    x = int(CANVAS_ROI["x"] * w)
    y = int(CANVAS_ROI["y"] * h)
    cw = int(CANVAS_ROI["w"] * w)
    ch = int(CANVAS_ROI["h"] * h)
    return frame[y:y+ch, x:x+cw]


def _resize_numpy(img: np.ndarray, w: int, h: int) -> np.ndarray:
    """Simple numpy resize (no cv2)."""
    from PIL import Image
    pil = Image.fromarray(img[:, :, ::-1])   # BGR→RGB
    pil = pil.resize((w, h))
    return np.array(pil)[:, :, ::-1]        # back to BGR


def _histogram_deviation(canvas: np.ndarray, ref: np.ndarray) -> float:
    """
    Compute per-channel histogram correlation.
    Returns an approximate delta-E value (0 = identical, higher = more different).
    """
    try:
        import cv2
        total_dist = 0.0
        for ch in range(3):
            h1 = cv2.calcHist([canvas], [ch], None, [64], [0, 256])
            h2 = cv2.calcHist([ref],    [ch], None, [64], [0, 256])
            cv2.normalize(h1, h1)
            cv2.normalize(h2, h2)
            # Bhattacharyya distance → scale to delta-E-like range
            dist = cv2.compareHist(h1, h2, cv2.HISTCMP_BHATTACHARYYA)
            total_dist += dist
        return round(total_dist * 15.0, 2)   # scale to ~0–45 range
    except ImportError:
        # numpy fallback: mean absolute channel difference
        diff = np.abs(canvas.astype(float).mean(axis=(0,1)) -
                      ref.astype(float).mean(axis=(0,1)))
        return round(float(diff.mean()) / 10.0, 2)


def _detect_stroke_errors(canvas: np.ndarray, ref: np.ndarray) -> list[StrokeError]:
    """
    Divide canvas into a 3×3 grid and detect which zones have high deviation.
    """
    errors: list[StrokeError] = []
    h, w = canvas.shape[:2]
    grid_h, grid_w = h // 3, w // 3

    ZONE_NAMES = [
        ["superior-izquierda", "superior-centro", "superior-derecha"],
        ["centro-izquierda",   "centro",           "centro-derecha"  ],
        ["inferior-izquierda", "inferior-centro",  "inferior-derecha"],
    ]
    THRESHOLD = 35.0   # mean pixel diff threshold per zone

    for row in range(3):
        for col in range(3):
            y0, y1 = row * grid_h, (row + 1) * grid_h
            x0, x1 = col * grid_w, (col + 1) * grid_w

            zone_canvas = canvas[y0:y1, x0:x1].astype(float)
            zone_ref    = ref[y0:y1, x0:x1].astype(float)
            zone_diff   = np.abs(zone_canvas - zone_ref).mean()

            if zone_diff > THRESHOLD:
                zone = ZONE_NAMES[row][col]
                # Characterize the dominant error
                ch_diff = (zone_canvas - zone_ref).mean(axis=(0, 1))  # B, G, R
                dominant = int(np.abs(ch_diff).argmax())
                channel_name = ["azul", "verde", "rojo"][dominant]
                if ch_diff[dominant] > 0:
                    msg = f"Exceso de {channel_name} — reduce pigmento"
                else:
                    msg = f"Falta {channel_name} — añade más pigmento"
                errors.append(StrokeError(zone=zone, message=msg))

    return errors


def _build_suggestions(precision: float, color_dev: float,
                        errors: list[StrokeError]) -> list[str]:
    tips: list[str] = []

    if precision >= 90:
        tips.append("¡Excelente trazo! Continúa con la misma técnica")
    elif precision >= 75:
        tips.append("Buen progreso — mejora la cobertura en las zonas marcadas")
    else:
        tips.append("Cubre bien el lienzo antes de agregar detalles")

    if color_dev > 10:
        tips.append("El color se aleja de la referencia — revisa la mezcla de pigmentos")
    elif color_dev > 5:
        tips.append("Pequeña desviación de color — ajusta levemente la mezcla")

    if len(errors) > 2:
        tips.append("Varias zonas con errores — trabaja de arriba hacia abajo")

    return tips
