"""
Vision analysis pipeline — stage-aware, activity-gated.

Flow:
  1. set_reference() loads the reference + captures a baseline frame (empty canvas)
  2. analyze() waits for painting activity before sending any feedback
  3. Feedback is limited to the stage objective — no irrelevant color reports
"""
import logging
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path

import calibration
from config import CANVAS_ROI, FRAME_WIDTH, FRAME_HEIGHT

logger = logging.getLogger(__name__)

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class StrokeError:
    zone: str
    message: str


@dataclass
class FeedbackResult:
    precision_pct: float
    color_deviation: float
    stroke_errors: list[StrokeError] = field(default_factory=list)
    suggestions: list[str]          = field(default_factory=list)


# ── Stage objective definitions ───────────────────────────────────────────────
# Each stage defines:
#   colors      — list of target colors with HSV ranges (OpenCV: H 0-180)
#   min_coverage — minimum % of the paintable area that should be covered
#   description — human-readable goal for logs

STAGE_OBJECTIVES: dict[tuple[str, int], dict] = {
    ("faro-nocturno", 1): {
        "description": "Rellena los contornos con amarillo",
        "colors": [
            {
                "name": "amarillo",
                # Yellow hue in OpenCV HSV: 15–35 (covers warm yellow + lemon yellow)
                "hsv_lower": (15, 60, 80),
                "hsv_upper": (35, 255, 255),
            },
        ],
        "min_coverage": 60.0,   # % of paintable area that must be yellow
        "activity_threshold": 10.0,   # mean pixel diff from baseline to count as "painting started"
    },
    ("faro-nocturno", 2): {
        "description": "Agrega tonos naranjas en la luz del faro",
        "colors": [
            {
                "name": "naranja",
                "hsv_lower": (5, 80, 80),
                "hsv_upper": (15, 255, 255),
            },
        ],
        "min_coverage": 30.0,
        "activity_threshold": 10.0,
    },
    ("faro-nocturno", 3): {
        "description": "Pinta el cielo nocturno con azul oscuro",
        "colors": [
            {
                "name": "azul oscuro",
                "hsv_lower": (100, 60, 30),
                "hsv_upper": (130, 255, 180),
            },
        ],
        "min_coverage": 50.0,
        "activity_threshold": 10.0,
    },
}

# Fallback activity threshold if stage not in STAGE_OBJECTIVES
DEFAULT_ACTIVITY_THRESHOLD = 10.0

# ── Global state ──────────────────────────────────────────────────────────────

_reference: np.ndarray | None = None
_reference_id: str = ""
_reference_stage: int = 0

# Baseline = first frame captured after set_reference() (empty canvas)
_baseline: np.ndarray | None = None
_baseline_samples: list[np.ndarray] = []
_BASELINE_FRAMES = 5     # average this many frames to build a stable baseline
_painting_active: bool = False

ANALYSIS_W, ANALYSIS_H = 320, 240


# ── Public API ────────────────────────────────────────────────────────────────

def set_reference(image_path: str, artwork_id: str, stage: int) -> bool:
    """Load a reference image and reset the baseline for the new stage."""
    global _reference, _reference_id, _reference_stage
    global _baseline, _baseline_samples, _painting_active

    try:
        import cv2
        path = Path(image_path)
        if not path.exists():
            logger.error("Reference not found: %s", image_path)
            return False

        img = cv2.imread(str(path))
        if img is None:
            logger.error("cv2.imread returned None for: %s", image_path)
            return False

        img = cv2.resize(img, (ANALYSIS_W, ANALYSIS_H))
        _reference       = img
        _reference_id    = artwork_id
        _reference_stage = stage

        # Reset baseline — will be captured from the next frames
        _baseline         = None
        _baseline_samples = []
        _painting_active  = False

        obj = STAGE_OBJECTIVES.get((artwork_id, stage))
        desc = obj["description"] if obj else "objetivo genérico"
        logger.info("Reference set: %s etapa %d — %s", artwork_id, stage, desc)
        return True

    except Exception as e:
        logger.error("set_reference error: %s", e)
        return False


def analyze(frame: np.ndarray) -> FeedbackResult | None:
    """
    Run stage-aware analysis on a frame.
    Returns None if:
      - No reference is loaded
      - Still building the baseline (first N frames)
      - No painting activity detected yet
    """
    global _baseline, _baseline_samples, _painting_active

    if _reference is None:
        return None

    try:
        import cv2

        # Preprocess frame
        corrected    = calibration.apply_color(frame)
        warped       = calibration.apply_homography(corrected)
        canvas       = _crop_roi(warped)
        canvas_small = cv2.resize(canvas, (ANALYSIS_W, ANALYSIS_H))

        # Phase 1: Build baseline from first N frames (empty canvas)
        if _baseline is None:
            _baseline_samples.append(canvas_small.astype(np.float32))
            if len(_baseline_samples) >= _BASELINE_FRAMES:
                _baseline = np.mean(_baseline_samples, axis=0).astype(np.uint8)
                logger.info("Baseline established (%d frames) — waiting for painting activity.", _BASELINE_FRAMES)
            return None   # no feedback yet while building baseline

        # Phase 2: Check for painting activity
        stage_obj = STAGE_OBJECTIVES.get((_reference_id, _reference_stage))
        act_thresh = stage_obj["activity_threshold"] if stage_obj else DEFAULT_ACTIVITY_THRESHOLD

        diff_from_baseline = np.abs(
            canvas_small.astype(np.float32) - _baseline.astype(np.float32)
        ).mean()

        if not _painting_active:
            if diff_from_baseline < act_thresh:
                return None   # canvas unchanged — no painting yet
            _painting_active = True
            logger.info("Painting activity detected (diff=%.1f) — analysis active.", diff_from_baseline)

        # Phase 3: Stage-aware analysis
        if stage_obj:
            return _analyze_stage(canvas_small, stage_obj)
        else:
            # Unknown stage — fall back to generic diff
            return _analyze_generic(canvas_small)

    except Exception as e:
        logger.error("Pipeline error: %s", e)
        return None


# ── Stage-aware analysis ──────────────────────────────────────────────────────

def _analyze_stage(canvas: np.ndarray, stage_obj: dict) -> FeedbackResult:
    """
    Analyze canvas against stage objectives (color coverage only).
    Only reports errors relevant to the stage's target colors.
    """
    import cv2

    colors   = stage_obj["colors"]
    min_cov  = stage_obj.get("min_coverage", 50.0)

    # Build mask of paintable area from reference (non-white, non-contour regions)
    paintable_mask = _get_paintable_mask(_reference)
    paintable_px   = int(paintable_mask.sum())
    if paintable_px == 0:
        paintable_px = canvas.shape[0] * canvas.shape[1]
        paintable_mask = np.ones((canvas.shape[0], canvas.shape[1]), dtype=bool)

    canvas_hsv = cv2.cvtColor(canvas, cv2.COLOR_BGR2HSV)

    errors: list[StrokeError] = []
    total_colored_px = 0

    for color_def in colors:
        lower = np.array(color_def["hsv_lower"], dtype=np.uint8)
        upper = np.array(color_def["hsv_upper"], dtype=np.uint8)
        color_mask = cv2.inRange(canvas_hsv, lower, upper).astype(bool)

        # Only count paint within the paintable area
        color_in_area = color_mask & paintable_mask
        colored_px    = int(color_in_area.sum())
        total_colored_px += colored_px

        coverage_pct = (colored_px / paintable_px) * 100.0
        logger.debug("%s coverage: %.1f%% (%d/%d px)", color_def["name"], coverage_pct, colored_px, paintable_px)

        if coverage_pct < min_cov:
            # Find which zones lack the color
            zone_errors = _find_uncovered_zones(color_in_area, paintable_mask, color_def["name"])
            errors.extend(zone_errors)

    # Check out-of-bounds painting (paint outside contour lines)
    contour_errors = _check_out_of_bounds(canvas_hsv, colors)
    errors.extend(contour_errors)

    # Overall precision = how much of the paintable area has the right color
    precision = min(100.0, (total_colored_px / paintable_px) * 100.0)

    # Color deviation: only for the target colors
    color_dev = _color_deviation_for_stage(canvas_hsv, colors)

    suggestions = _build_stage_suggestions(precision, errors, stage_obj)

    return FeedbackResult(
        precision_pct=round(precision, 1),
        color_deviation=round(color_dev, 2),
        stroke_errors=errors,
        suggestions=suggestions,
    )


def _analyze_generic(canvas: np.ndarray) -> FeedbackResult:
    """Fallback when stage has no defined objective — pure pixel diff."""
    diff    = np.abs(canvas.astype(np.int16) - _reference.astype(np.int16))
    mean_d  = float(diff.mean())
    prec    = max(0.0, min(100.0, 100.0 - (mean_d / 255.0) * 100.0))
    color_d = _histogram_deviation(canvas, _reference)
    tips    = ["Sigue la referencia de la etapa actual"]
    return FeedbackResult(precision_pct=round(prec, 1), color_deviation=round(color_d, 2), suggestions=tips)


# ── Zone helpers ──────────────────────────────────────────────────────────────

_ZONE_NAMES = [
    ["superior-izquierda", "superior-centro", "superior-derecha"],
    ["centro-izquierda",   "centro",           "centro-derecha"  ],
    ["inferior-izquierda", "inferior-centro",  "inferior-derecha"],
]


def _find_uncovered_zones(color_mask: np.ndarray, paintable_mask: np.ndarray,
                           color_name: str) -> list[StrokeError]:
    """Return a StrokeError for each grid zone that lacks the target color."""
    errors: list[StrokeError] = []
    h, w = color_mask.shape[:2]
    gh, gw = h // 3, w // 3

    for row in range(3):
        for col in range(3):
            y0, y1 = row * gh, (row + 1) * gh
            x0, x1 = col * gw, (col + 1) * gw
            zone_paintable = paintable_mask[y0:y1, x0:x1].sum()
            if zone_paintable < 50:
                continue   # zone is mostly contour lines — skip
            zone_colored   = color_mask[y0:y1, x0:x1].sum()
            zone_cov       = (zone_colored / zone_paintable) * 100.0
            if zone_cov < 30.0:
                errors.append(StrokeError(
                    zone=_ZONE_NAMES[row][col],
                    message=f"Falta {color_name} — cubre esta zona",
                ))
    return errors


def _check_out_of_bounds(canvas_hsv: np.ndarray,
                          colors: list[dict]) -> list[StrokeError]:
    """Detect any paint (of the target colors) outside the contour boundaries."""
    import cv2

    contour_mask = _get_contour_mask(_reference)
    if contour_mask is None:
        return []

    errors: list[StrokeError] = []
    for color_def in colors:
        lower = np.array(color_def["hsv_lower"], dtype=np.uint8)
        upper = np.array(color_def["hsv_upper"], dtype=np.uint8)
        paint_mask  = cv2.inRange(canvas_hsv, lower, upper).astype(bool)
        outside_px  = int((paint_mask & contour_mask).sum())
        if outside_px > 80:    # more than ~80 pixels outside = meaningful error
            errors.append(StrokeError(
                zone="contorno",
                message=f"Pintura de {color_def['name']} fuera del contorno — mantente dentro de las líneas",
            ))
            break
    return errors


# ── Mask helpers ──────────────────────────────────────────────────────────────

def _get_paintable_mask(ref: np.ndarray) -> np.ndarray:
    """
    Returns boolean mask of pixels that should be painted.
    "Paintable" = not white background AND not black contour line.
    For Etapa 1 reference images (white bg + black lines + colored fill):
    we look for non-white, non-black pixels OR simply the non-white area
    that isn't the contour.
    """
    import cv2
    gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    # White background: pixel > 220
    # Black contour:    pixel < 40
    # Paintable area: everything in between (or already filled with color)
    paintable = (gray > 40) & (gray < 230)
    if paintable.sum() < 100:
        # Reference might be fully white/blank — treat entire canvas as paintable
        paintable = np.ones((ref.shape[0], ref.shape[1]), dtype=bool)
    return paintable


def _get_contour_mask(ref: np.ndarray) -> np.ndarray | None:
    """Returns boolean mask of contour line pixels (dark lines in reference)."""
    import cv2
    try:
        gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
        # Dark pixels = contour lines
        _, contour = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
        return contour.astype(bool)
    except Exception:
        return None


# ── Color deviation ───────────────────────────────────────────────────────────

def _color_deviation_for_stage(canvas_hsv: np.ndarray, colors: list[dict]) -> float:
    """
    Measure how close the painted color is to the ideal target hue.
    Returns 0 = perfect, higher = further from target.
    """
    import cv2

    if not colors:
        return 0.0

    deviations = []
    for color_def in colors:
        lower = np.array(color_def["hsv_lower"], dtype=np.uint8)
        upper = np.array(color_def["hsv_upper"], dtype=np.uint8)
        mask  = cv2.inRange(canvas_hsv, lower, upper)
        px    = int(mask.sum() / 255)
        if px < 50:
            deviations.append(30.0)   # color is missing — high deviation
            continue
        # Mean hue of painted pixels within range
        hue_channel = canvas_hsv[:, :, 0]
        painted_hues = hue_channel[mask > 0].astype(float)
        ideal_hue    = (int(lower[0]) + int(upper[0])) / 2.0
        hue_dev      = float(np.abs(painted_hues - ideal_hue).mean())
        deviations.append(hue_dev)

    return round(float(np.mean(deviations)), 2)


def _histogram_deviation(canvas: np.ndarray, ref: np.ndarray) -> float:
    """Generic per-channel histogram distance (used for unknown stages)."""
    try:
        import cv2
        total = 0.0
        for ch in range(3):
            h1 = cv2.calcHist([canvas], [ch], None, [64], [0, 256])
            h2 = cv2.calcHist([ref],    [ch], None, [64], [0, 256])
            cv2.normalize(h1, h1)
            cv2.normalize(h2, h2)
            total += cv2.compareHist(h1, h2, cv2.HISTCMP_BHATTACHARYYA)
        return round(total * 15.0, 2)
    except Exception:
        return 0.0


# ── Suggestions ───────────────────────────────────────────────────────────────

def _build_stage_suggestions(precision: float, errors: list[StrokeError],
                               stage_obj: dict) -> list[str]:
    tips: list[str] = []
    color_names = [c["name"] for c in stage_obj.get("colors", [])]
    color_str   = " y ".join(color_names) if color_names else "el color correcto"

    if precision >= 85:
        tips.append(f"¡Excelente! Casi toda la zona está cubierta de {color_str}")
    elif precision >= 60:
        tips.append(f"Buen progreso — sigue cubriendo con {color_str}")
    elif precision >= 30:
        tips.append(f"Continúa — cubre más área con {color_str}")
    else:
        tips.append(f"Aplica {color_str} dentro de los contornos del dibujo")

    contour_errors = [e for e in errors if e.zone == "contorno"]
    if contour_errors:
        tips.append("Cuidado: hay pintura fuera de las líneas — mantente dentro del contorno")

    return tips


# ── ROI crop ──────────────────────────────────────────────────────────────────

def _crop_roi(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    x  = int(CANVAS_ROI["x"] * w)
    y  = int(CANVAS_ROI["y"] * h)
    cw = int(CANVAS_ROI["w"] * w)
    ch = int(CANVAS_ROI["h"] * h)
    return frame[y:y+ch, x:x+cw]
