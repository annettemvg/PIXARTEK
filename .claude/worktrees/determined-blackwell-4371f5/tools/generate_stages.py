#!/usr/bin/env python3
"""
PIXARTEK Stage Image Generator — Mujer Azul (Cándido Bidó, 1988)
11 cumulative oil-painting stages. Every image simulates a real photograph
of a real canvas at that exact moment of creation. Faithful to the reference.
"""
import argparse, datetime, logging, math, os, sqlite3, sys, time, uuid
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# ── Output paths ──────────────────────────────────────────────────────────────
ARTWORK_ID  = "mujer-azul"
ASSETS_ROOT = Path(__file__).parent.parent / "assets"
OUTPUT_DIR  = ASSETS_ROOT / "stages" / "mujer_azul"
LOG_DIR     = Path("/var/log/pixartek")
DB_PATHS    = [
    Path(__file__).parent.parent / "backend" / "pixartek.db",
    Path("/home/pi/pixartek/data/pixartek.db"),
]

# ── Canvas / projection sizes ─────────────────────────────────────────────────
W, H       = 527, 631          # matches reference photo aspect ratio
PROJ_W     = 1920
PROJ_H     = 1080
PROJ_BG    = (13, 28, 72)

# ── Exact palette sampled from Bidó "Rostro Azul" 1988 ───────────────────────
PAL = {
    "bg_prussian":   (26,  47, 110),
    "bg_dark":       (12,  22,  65),
    "bg_cobalt":     (43,  91, 168),
    "bg_violet":     (55,  72, 130),
    "bg_mid":        (35,  65, 140),
    "face_periwinkle":(123,158,200),
    "face_shadow":   ( 85,120,165),
    "face_light":    (165,195,225),
    "face_neck":     (100,135,178),
    "cover_white":   (214,228,240),
    "cover_shadow":  (185,205,225),
    "cover_dot":     ( 65,115,185),
    "outline":       ( 12,  12,  16),
    "eye_white":     (195,215,232),
    "moon_white":    (232,240,248),
    "moon_glow":     (175,205,230),
    "linen":         (245,241,232),
    "linen_shadow":  (228,222,210),
    "charcoal":      (110,105,115),
    "charcoal_faint":(175,170,178),
}

# ── Geometry calibrated to reference painting ─────────────────────────────────
# Face — large oval, centered, slightly below mid-canvas
FCX, FCY, FRX, FRY = 263, 380, 175, 195          # center x,y; radius x,y
FACE_BOX = (FCX-FRX, FCY-FRY, FCX+FRX, FCY+FRY)

# Neck — short rectangle below face
NECK = (226, 545, 302, 625)

# Head covering — rounded rectangle sitting on top of / around the head
HCOX, HCOY = 263, 270          # covering center
HCRX, HCRY = 175, 130          # covering radii
COVER_BOX = (HCOX-HCRX, HCOY-HCRY, HCOX+HCRX, HCOY+HCRY)

# Eyes — large dark almonds
EYE_L = (170, 342, 240, 388)
EYE_R = (286, 342, 356, 388)

# Nose center
NCX, NY0, NY1 = 263, 405, 445

# Mouth center
MCX, MCY, MW, MH = 263, 488, 68, 24

# Moon — upper left
MOON_CX, MOON_CY, MOON_R = 62,  68,  38

# Background panel geometry
VSTRIPE_X0, VSTRIPE_X1 = 230, 298          # dark vertical stripe above head
RIGHT_PANEL_X = 355                          # right-side stippled area


# ── Logging ───────────────────────────────────────────────────────────────────
def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    handlers = [logging.StreamHandler(sys.stdout)]
    try:
        handlers.append(logging.FileHandler(LOG_DIR / "stage_generation.log"))
    except PermissionError:
        pass
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)
    return logging.getLogger("pixartek.stages")


# ── Primitive helpers ─────────────────────────────────────────────────────────
def _rng(seed=None):
    return np.random.default_rng(seed)


def _canvas_linen(seed=0):
    """Cream linen canvas texture — base for unpainted areas."""
    rng = _rng(seed)
    arr = np.full((H, W, 3), PAL["linen"], dtype=np.float32)
    for y in range(0, H, 2):
        arr[y, :] += rng.uniform(-3, 3)
    for x in range(0, W, 3):
        arr[:, x] += rng.uniform(-2.5, 2.5)
    arr += rng.normal(0, 2.5, arr.shape)
    for _ in range(10):
        cx, cy = rng.integers(0, W), rng.integers(0, H)
        r = rng.integers(15, 55)
        yy, xx = np.ogrid[-cy:H-cy, -cx:W-cx]
        mask = (xx**2 + yy**2) < r**2
        arr[mask] -= rng.uniform(4, 12)
    return np.clip(arr, 195, 255).astype(np.uint8)


def _ellipse_mask(box, feather=0):
    x0, y0, x1, y1 = box
    cx, cy = (x0+x1)/2, (y0+y1)/2
    rx, ry = (x1-x0)/2, (y1-y0)/2
    yy, xx = np.mgrid[0:H, 0:W]
    dist = ((xx-cx)/max(rx,1))**2 + ((yy-cy)/max(ry,1))**2
    if feather <= 0:
        return (dist <= 1.0).astype(np.float32)
    return np.clip(1.0 - (dist**0.5 - 1.0)/(feather/min(rx, ry)), 0, 1).astype(np.float32)


def _rect_mask(box, feather=0):
    x0, y0, x1, y1 = [int(v) for v in box]
    m = np.zeros((H, W), np.float32)
    m[y0:y1, x0:x1] = 1.0
    if feather > 0:
        from scipy.ndimage import gaussian_filter
        m = gaussian_filter(m, sigma=feather)
    return m


def _poly_mask(pts):
    img = Image.new("L", (W, H), 0)
    ImageDraw.Draw(img).polygon(pts, fill=255)
    return np.array(img).astype(np.float32) / 255.0


def _paint_layer(color, direction="h", noise=12, sw=16, seed=0):
    """Full-canvas paint layer with directional brushstroke texture."""
    rng = _rng(seed)
    arr = np.full((H, W, 3), color, dtype=np.float32)
    arr += rng.normal(0, noise, arr.shape)

    if direction == "h":
        y = 0
        while y < H:
            bh = rng.integers(max(2, sw//3), sw//2 + 1)
            arr[y:y+bh] += rng.normal(0, noise*0.55)
            y += bh
    elif direction == "v":
        x = 0
        while x < W:
            bw = rng.integers(max(2, sw//3), sw//2 + 1)
            arr[:, x:x+bw] += rng.normal(0, noise*0.55)
            x += bw
    elif direction == "d":
        for i in range(-H, W, rng.integers(sw, sw*2)):
            for yi in range(H):
                xi = i + yi
                if 0 <= xi < W:
                    bw = rng.integers(2, 5)
                    arr[yi, xi:xi+bw] += rng.normal(0, noise*0.45)

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.9))
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=28, threshold=4))
    return np.array(img)


def _apply(canvas, mask, paint, alpha=0.93):
    result = canvas.copy().astype(np.float32)
    m = np.clip(mask, 0, 1)[:, :, None]
    result = result * (1 - m*alpha) + paint.astype(np.float32) * m*alpha
    return np.clip(result, 0, 255).astype(np.uint8)


def _line(arr, p0, p1, color, width=3, noise=2, seed=0):
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    x0, y0 = p0; x1, y1 = p1
    n = max(int(math.hypot(x1-x0, y1-y0)/7), 2)
    pts = []
    for i in range(n+1):
        t = i/n
        x = x0 + (x1-x0)*t + rng.normal(0, noise)
        y = y0 + (y1-y0)*t + rng.normal(0, noise)
        pts.append((int(x), int(y)))
    for i in range(len(pts)-1):
        w = width + rng.integers(-1, 2)
        draw.line([pts[i], pts[i+1]], fill=color, width=max(1, w))
    return np.array(img)


def _ellipse_stroke(arr, box, color, width=4, noise=2, fill=None, seed=0):
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    bx0, by0, bx1, by1 = box
    cx, cy = (bx0+bx1)//2, (by0+by1)//2
    rx, ry = (bx1-bx0)//2, (by1-by0)//2
    if fill is not None:
        draw.ellipse([bx0, by0, bx1, by1], fill=fill)
    pts = []
    for i in range(65):
        a = 2*math.pi*i/64
        x = cx + rx*math.cos(a) + rng.normal(0, noise)
        y = cy + ry*math.sin(a) + rng.normal(0, noise)
        pts.append((int(x), int(y)))
    for i in range(len(pts)-1):
        w = width + rng.integers(-1, 2)
        draw.line([pts[i], pts[i+1]], fill=color, width=max(1, w))
    return np.array(img)


# ── Composite masks ───────────────────────────────────────────────────────────
def _bg_mask():
    face_m  = _ellipse_mask(FACE_BOX, feather=7)
    neck_m  = _rect_mask(NECK)
    cover_m = _ellipse_mask(COVER_BOX, feather=7)
    figure  = np.clip(face_m + neck_m + cover_m, 0, 1)
    return np.clip(1 - figure, 0, 1)


def _face_mask():
    face_m  = _ellipse_mask(FACE_BOX, feather=5)
    cover_m = _ellipse_mask(COVER_BOX, feather=5)
    return np.clip(face_m * (1 - cover_m*0.65), 0, 1)


def _cover_mask():
    m = _ellipse_mask(COVER_BOX, feather=5).copy()
    cutoff = FCY - int(FRY * 0.08)
    m[cutoff:, :] = 0
    return m


# ══════════════════════════════════════════════════════════════════════════════
# STAGE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def stage_01(linen):
    """White canvas + light charcoal composition sketch."""
    arr = linen.copy()
    cd = PAL["charcoal"]
    cl = PAL["charcoal_faint"]

    # Head circle
    arr = _ellipse_stroke(arr, FACE_BOX, cd, width=2, noise=1.5, seed=1)
    # Head covering
    arr = _ellipse_stroke(arr, COVER_BOX, cl, width=1, noise=2, seed=2)
    # Neck
    for seg in [((NECK[0], NECK[1]), (NECK[0], NECK[3])),
                ((NECK[2], NECK[1]), (NECK[2], NECK[3])),
                ((NECK[0], NECK[3]), (NECK[2], NECK[3]))]:
        arr = _line(arr, seg[0], seg[1], cd, width=2, noise=1, seed=3)
    # Vertical stripe lines
    arr = _line(arr, (VSTRIPE_X0, 0), (VSTRIPE_X0, FCY-FRY-8), cl, width=1, noise=1, seed=4)
    arr = _line(arr, (VSTRIPE_X1, 0), (VSTRIPE_X1, FCY-FRY-8), cl, width=1, noise=1, seed=5)
    # Horizontal grid lines (architectural)
    rng = _rng(6)
    for y in range(35, FCY-FRY-15, int(rng.integers(22, 38))):
        arr = _line(arr, (0, y), (W, y+rng.integers(-3,3)), cl, width=1, noise=2, seed=y)
    # Moon
    mb = (MOON_CX-MOON_R, MOON_CY-MOON_R, MOON_CX+MOON_R, MOON_CY+MOON_R)
    arr = _ellipse_stroke(arr, mb, cl, width=1, noise=1.5, seed=7)
    # Eye guides
    for eb, s in [(EYE_L, 8), (EYE_R, 9)]:
        arr = _ellipse_stroke(arr, eb, cl, width=1, noise=1, seed=s)
    # Nose guide
    arr = _line(arr, (NCX, NY0), (NCX, NY1), cl, width=1, noise=1, seed=10)
    return arr


def stage_02(prev, linen):
    """Background first coat — prussian blue horizontal brushstrokes."""
    arr = prev.copy()
    bg = _bg_mask()
    p1 = _paint_layer(PAL["bg_prussian"], "h", noise=13, sw=22, seed=10)
    arr = _apply(arr, bg, p1, alpha=0.97)
    # second coat variation
    p2 = _paint_layer(PAL["bg_mid"], "h", noise=9, sw=30, seed=11)
    arr = _apply(arr, bg*0.3, p2, alpha=0.45)
    return arr


def stage_03(prev):
    """Background panels, architectural lines, moon blocked in."""
    arr = prev.copy()
    bg = _bg_mask()
    rng = _rng(20)

    # ── Darker vertical stripe above head ──
    stripe_m = _rect_mask((VSTRIPE_X0, 0, VSTRIPE_X1, FCY-FRY+15)) * bg
    sp = _paint_layer(PAL["bg_dark"], "v", noise=7, sw=12, seed=21)
    arr = _apply(arr, stripe_m, sp, alpha=0.68)

    # ── Horizontal architectural lines ──
    img = Image.fromarray(arr); draw = ImageDraw.Draw(img)
    y = 30
    while y < FCY - FRY - 5:
        step = int(rng.integers(20, 36))
        thick = rng.integers(2, 5)
        a = rng.uniform(0.35, 0.62)
        lc = tuple(int(PAL["bg_dark"][i]*a + PAL["bg_prussian"][i]*(1-a)) for i in range(3))
        draw.line([(rng.integers(0,15), y), (W-rng.integers(0,15), y+rng.integers(-2,2))],
                  fill=lc, width=thick)
        y += step
    arr = np.array(img)

    # ── Right panel stippled dots ──
    img = Image.fromarray(arr); draw = ImageDraw.Draw(img)
    drng = _rng(22)
    for _ in range(200):
        dx = drng.integers(RIGHT_PANEL_X, W-8)
        dy = drng.integers(8, H-8)
        if bg[min(dy,H-1), min(dx,W-1)] > 0.4:
            dr = drng.integers(2, 7)
            a  = drng.uniform(0.4, 0.82)
            dc = PAL["bg_dark"] if drng.random() > 0.4 else PAL["bg_cobalt"]
            px = arr[min(dy,H-1), min(dx,W-1)]
            fc = tuple(int(dc[i]*a + px[i]*(1-a)) for i in range(3))
            draw.ellipse([dx-dr, dy-dr, dx+dr, dy+dr], fill=fc)
    arr = np.array(img)

    # ── Moon — blocked in ──
    mo = MOON_R + 7
    mb = (MOON_CX-mo, MOON_CY-mo, MOON_CX+mo, MOON_CY+mo)
    mm = _ellipse_mask(mb, feather=10)
    mp = _paint_layer(PAL["moon_glow"], "d", noise=7, seed=23)
    arr = _apply(arr, mm, mp, alpha=0.87)
    mb2 = (MOON_CX-MOON_R+3, MOON_CY-MOON_R+3, MOON_CX+MOON_R-3, MOON_CY+MOON_R-3)
    mm2 = _ellipse_mask(mb2, feather=5)
    mp2 = _paint_layer(PAL["moon_white"], "d", noise=5, seed=24)
    arr = _apply(arr, mm2, mp2, alpha=0.80)

    return arr


def stage_04(prev, linen):
    """Face and neck filled with periwinkle blue base coat."""
    arr = prev.copy()
    fm = _face_mask()
    nm = _rect_mask(NECK)

    fp = _paint_layer(PAL["face_periwinkle"], "d", noise=10, sw=16, seed=30)
    arr = _apply(arr, fm, fp, alpha=0.95)

    np2 = _paint_layer(PAL["face_neck"], "v", noise=8, sw=12, seed=31)
    arr = _apply(arr, nm, np2, alpha=0.95)
    return arr


def stage_05(prev):
    """Head covering base (off-white) + cobalt dot row along edge."""
    arr = prev.copy()
    cm = _cover_mask()

    cp = _paint_layer(PAL["cover_white"], "h", noise=6, sw=18, seed=40)
    arr = _apply(arr, cm, cp, alpha=0.97)

    # shadow at edges
    inner = _ellipse_mask(
        (HCOX-HCRX+22, HCOY-HCRY+22, HCOX+HCRX-22, HCOY+HCRY-22), feather=18)
    edge_m = cm * (1 - inner*0.72)
    sp = _paint_layer(PAL["cover_shadow"], "h", noise=4, seed=41)
    arr = _apply(arr, edge_m*0.45, sp, alpha=0.55)

    # ── Cobalt dots along curved bottom edge of covering ──
    img = Image.fromarray(arr); draw = ImageDraw.Draw(img)
    n_dots = 13
    for i in range(n_dots):
        t = i / (n_dots - 1)
        angle = math.pi * (0.10 + 0.80 * t)
        px = int(HCOX + (HCRX - 18) * math.cos(math.pi - angle))
        py = int(HCOY + int(HCRY * 0.72) * abs(math.sin(angle)) - 16)
        dr = 7
        draw.ellipse([px-dr, py-dr, px+dr, py+dr], fill=PAL["cover_dot"])
        draw.ellipse([px-2, py-3, px+2, py], fill=(180, 210, 245))
    arr = np.array(img)
    return arr


def stage_06(prev):
    """Black painterly outlines defining all major shapes."""
    arr = prev.copy()
    c = PAL["outline"]

    # Head circle
    arr = _ellipse_stroke(arr, FACE_BOX, c, width=4, noise=2, seed=50)
    # Neck
    arr = _line(arr, (NECK[0], NECK[1]-4), (NECK[0], NECK[3]), c, width=3, noise=1.5, seed=51)
    arr = _line(arr, (NECK[2], NECK[1]-4), (NECK[2], NECK[3]), c, width=3, noise=1.5, seed=52)
    arr = _line(arr, (NECK[0], NECK[3]), (NECK[2], NECK[3]), c, width=3, noise=1.5, seed=53)
    # Forehead division (face/covering boundary) — gentle arc
    div_y = FCY - FRY + int(FRY * 0.28)
    pts = []
    for xi in range(FCX-FRX+18, FCX+FRX-18, 7):
        t = (xi - FCX) / FRX
        yi = div_y + int(14*t**2)
        pts.append((xi, yi))
    for i in range(len(pts)-1):
        arr = _line(arr, pts[i], pts[i+1], c, width=3, noise=1.5, seed=54+i)
    # Covering outer edge
    arr = _ellipse_stroke(arr, COVER_BOX, c, width=3, noise=2, seed=60)
    # Neck-face junction
    jy = NECK[1] + 6
    arr = _line(arr, (NECK[0]-8, jy), (NECK[2]+8, jy), c, width=2, noise=1.5, seed=61)
    return arr


def stage_07(prev):
    """Two large dark almond eyes with inner light crescent."""
    arr = prev.copy()
    img = Image.fromarray(arr); draw = ImageDraw.Draw(img)
    for eye_box, seed in [(EYE_L, 70), (EYE_R, 71)]:
        ex0, ey0, ex1, ey1 = eye_box
        draw.ellipse([ex0, ey0, ex1, ey1], fill=PAL["outline"])
        # inner light crescent
        ecx = (ex0+ex1)//2
        ix = ex0 + 7 if eye_box is EYE_L else ex1 - 7
        draw.ellipse([ix-5, ey0+7, ix+5, ey1-7], fill=PAL["eye_white"])
    arr = np.array(img)
    for eye_box, seed in [(EYE_L, 72), (EYE_R, 73)]:
        arr = _ellipse_stroke(arr, eye_box, PAL["outline"], width=2, noise=1.5, seed=seed)
    return arr


def stage_08(prev):
    """Minimal nose — 3-4 dark vertical brushstrokes."""
    arr = prev.copy()
    c = PAL["outline"]
    for dx, s in [(-9, 80), (9, 81)]:
        arr = _line(arr, (NCX+dx, NY0), (NCX+dx, NY1-10), c, width=2, noise=1.5, seed=s)
    arr = _line(arr, (NCX-13, NY1), (NCX+13, NY1), c, width=2, noise=1.5, seed=82)
    arr = _line(arr, (NCX-13, NY1), (NCX-8, NY1-7), c, width=2, noise=1, seed=83)
    arr = _line(arr, (NCX+13, NY1), (NCX+8, NY1-7), c, width=2, noise=1, seed=84)
    return arr


def stage_09(prev):
    """Small lips — dark outline + lighter blue-gray fill."""
    arr = prev.copy()
    img = Image.fromarray(arr); draw = ImageDraw.Draw(img)
    mx0, mx1 = MCX-MW//2, MCX+MW//2
    my0, my1 = MCY-MH//2, MCY+MH//2
    lip_fill = tuple(int(c*0.76 + 255*0.24) for c in PAL["face_periwinkle"])
    draw.ellipse([mx0, my0, mx1, my1], fill=lip_fill)
    mid_y = (my0+my1)//2
    draw.line([(mx0+4, mid_y), (mx1-4, mid_y)], fill=PAL["outline"], width=2)
    arr = np.array(img)
    arr = _ellipse_stroke(arr, (mx0, my0, mx1, my1), PAL["outline"], width=2, noise=1.5, seed=90)
    # cupid's bow
    arr = _line(arr, (MCX-10, my0), (MCX, my0+6), PAL["outline"], width=2, noise=1, seed=91)
    arr = _line(arr, (MCX+10, my0), (MCX, my0+6), PAL["outline"], width=2, noise=1, seed=92)
    return arr


def stage_10(prev):
    """Second face layer — volume with shadow and light strokes."""
    arr = prev.copy()
    fm = _face_mask()

    # Shadow — sides of face
    sl = _ellipse_mask((FCX-FRX, FCY-int(FRY*0.3), FCX-int(FRX*0.3), FCY+FRY), feather=28)
    sr = _ellipse_mask((FCX+int(FRX*0.3), FCY-int(FRY*0.3), FCX+FRX, FCY+FRY), feather=28)
    sm = np.clip(sl+sr, 0, 1) * fm
    sp = _paint_layer(PAL["face_shadow"], "d", noise=8, seed=100)
    arr = _apply(arr, sm, sp, alpha=0.50)

    # Highlight — center forehead / nose bridge
    hm = _ellipse_mask((FCX-int(FRX*0.25), FCY-FRY+18, FCX+int(FRX*0.25), FCY-int(FRY*0.12)),
                       feather=22) * fm
    hp = _paint_layer(PAL["face_light"], "d", noise=6, seed=101)
    arr = _apply(arr, hm, hp, alpha=0.42)

    # Nose bridge highlight
    nh = _ellipse_mask((NCX-15, NY0-22, NCX+15, NY1-8), feather=10) * fm
    arr = _apply(arr, nh, hp, alpha=0.28)
    return arr


def stage_11(prev):
    """Final unification — background enriched, moon refined, glaze applied."""
    arr = prev.copy()
    bg = _bg_mask()
    rng = _rng(110)

    # ── Extra background brushmarks ──
    img = Image.fromarray(arr); draw = ImageDraw.Draw(img)
    for _ in range(50):
        x0 = rng.integers(0, W)
        y0 = rng.integers(0, H)
        x1 = x0 + rng.integers(-50, 50)
        y1 = y0 + rng.integers(-6,  6)
        if 0<=x1<W and 0<=y1<H and bg[min(y0,H-1), min(x0,W-1)] > 0.45:
            tone = PAL["bg_cobalt"] if rng.random() > 0.5 else PAL["bg_dark"]
            a = rng.uniform(0.28, 0.60)
            px = arr[min(y0,H-1), min(x0,W-1)]
            sc = tuple(int(tone[i]*a + px[i]*(1-a)) for i in range(3))
            draw.line([(x0,y0),(x1,y1)], fill=sc, width=rng.integers(2,5))
    arr = np.array(img)

    # ── Moon — refined with concentric glow strokes ──
    img = Image.fromarray(arr); draw = ImageDraw.Draw(img)
    for ring_r in [MOON_R+12, MOON_R+7, MOON_R+2]:
        n = 44
        a_ring = 0.22 + (MOON_R + 12 - ring_r)*0.04
        for i in range(n):
            a0 = 2*math.pi*i/n + rng.uniform(-0.04, 0.04)
            a1 = 2*math.pi*(i+1)/n
            x0 = int(MOON_CX + ring_r*math.cos(a0))
            y0 = int(MOON_CY + ring_r*math.sin(a0))
            x1 = int(MOON_CX + ring_r*math.cos(a1))
            y1 = int(MOON_CY + ring_r*math.sin(a1))
            mc = PAL["moon_glow"] if ring_r > MOON_R else PAL["moon_white"]
            px = arr[min(y0,H-1), min(x0,W-1)]
            sc = tuple(int(mc[i]*a_ring + px[i]*(1-a_ring)) for i in range(3))
            draw.line([(x0,y0),(x1,y1)], fill=sc, width=2)
    draw.ellipse([MOON_CX-MOON_R+2, MOON_CY-MOON_R+2, MOON_CX+MOON_R-2, MOON_CY+MOON_R-2],
                 fill=PAL["moon_white"])
    arr = np.array(img)

    # ── Neck slightly darker ──
    nm = _rect_mask(NECK)
    np2 = _paint_layer(PAL["face_neck"], "v", noise=6, seed=111)
    arr = _apply(arr, nm*0.35, np2, alpha=0.50)

    # ── Thin unifying glaze over entire canvas ──
    glaze = np.full((H, W, 3), PAL["bg_prussian"], np.float32)
    arr = np.clip(arr.astype(np.float32)*0.965 + glaze*0.035, 0, 255).astype(np.uint8)

    # ── Final sharpening — impasto edge crispness ──
    img = Image.fromarray(arr)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.1, percent=22, threshold=5))
    return np.array(img)


# ── Stage pipeline ─────────────────────────────────────────────────────────────
STAGE_DEFS = [
    (1,  "El boceto — lienzo en blanco",           stage_01),
    (2,  "Primera capa del fondo — azul prusiano",  stage_02),
    (3,  "Textura del fondo, paneles y luna",       stage_03),
    (4,  "Base del rostro y el cuello",             stage_04),
    (5,  "Cubierta de la cabeza y puntos cobalto",  stage_05),
    (6,  "Contornos negros principales",            stage_06),
    (7,  "Ojos — grandes cuencas oscuras",          stage_07),
    (8,  "Nariz — trazos mínimos",                  stage_08),
    (9,  "Boca — contorno y relleno",               stage_09),
    (10, "Volumen del rostro — luces y sombras",    stage_10),
    (11, "Unificación final y detalles",            stage_11),
]


# ── Projection letterbox ───────────────────────────────────────────────────────
def make_projection(img):
    ow, oh = img.size
    scale = min(PROJ_W/ow, PROJ_H/oh)
    nw, nh = int(ow*scale), int(oh*scale)
    r = img.resize((nw, nh), Image.LANCZOS)
    proj = Image.new("RGB", (PROJ_W, PROJ_H), PROJ_BG)
    proj.paste(r, ((PROJ_W-nw)//2, (PROJ_H-nh)//2))
    return proj


# ── Validation ─────────────────────────────────────────────────────────────────
def validate(path, ew, eh, log):
    if not path.exists() or path.stat().st_size == 0:
        log.error("FAIL: %s missing/empty", path); return False
    img = Image.open(path)
    if img.size != (ew, eh):
        log.error("FAIL: %s size %s != (%d,%d)", path, img.size, ew, eh); return False
    log.info("  ✓ %s  %dx%d  %dKB", path.name, ew, eh, path.stat().st_size//1024)
    return True


# ── Database ───────────────────────────────────────────────────────────────────
def find_db():
    for p in DB_PATHS:
        if p.exists(): return p
    return None


def insert_stages(rows, log, dry_run=False):
    db_path = find_db()
    if db_path is None:
        log.warning("DB not found — skipping DB insert"); return
    if dry_run:
        log.info("[DRY RUN] Would insert %d rows", len(rows)); return
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS artwork_stages (
        stage_id TEXT PRIMARY KEY, artwork_id TEXT NOT NULL,
        stage_number INTEGER NOT NULL, image_path TEXT NOT NULL,
        projection_image_path TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("DELETE FROM artwork_stages WHERE artwork_id=?", (ARTWORK_ID,))
    now = datetime.datetime.utcnow().isoformat()
    for r in rows:
        cur.execute(
            "INSERT INTO artwork_stages (stage_id,artwork_id,stage_number,image_path,projection_image_path,created_at) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), r["artwork_id"], r["stage_number"],
             r["image_path"], r["projection_image_path"], now))
    conn.commit(); conn.close()
    log.info("Inserted %d rows into %s", len(rows), db_path)


# ── Main pipeline ──────────────────────────────────────────────────────────────
def run(dry_run, log):
    np.random.seed(42)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    log.info("Generating linen canvas base…")
    linen = _canvas_linen(seed=0)

    db_rows = []
    all_ok  = True
    prev    = linen.copy()

    for snum, sname, fn in STAGE_DEFS:
        t0 = time.perf_counter()
        log.info("Stage %02d/11 — %s", snum, sname)

        # call with (prev, linen) or just (prev) depending on signature
        import inspect
        sig = inspect.signature(fn)
        if len(sig.parameters) == 2:
            state = fn(prev, linen)
        else:
            state = fn(prev)
        prev = state.copy()

        out_p  = OUTPUT_DIR / f"stage_{snum:02d}.png"
        proj_p = OUTPUT_DIR / f"proj_stage_{snum:02d}.png"

        stage_img = Image.fromarray(state)
        proj_img  = make_projection(stage_img)

        if not dry_run:
            stage_img.save(out_p,  "PNG")
            proj_img.save(proj_p,  "PNG")
            ok1 = validate(out_p,  W,      H,      log)
            ok2 = validate(proj_p, PROJ_W, PROJ_H, log)
            all_ok = all_ok and ok1 and ok2

        elapsed = time.perf_counter() - t0
        log.info("  done in %.2fs", elapsed)

        rel_out  = str(out_p.relative_to(Path(__file__).parent.parent))
        rel_proj = str(proj_p.relative_to(Path(__file__).parent.parent))
        db_rows.append({"artwork_id": ARTWORK_ID, "stage_number": snum,
                         "image_path": rel_out, "projection_image_path": rel_proj})

    insert_stages(db_rows, log, dry_run)
    log.info("="*60)
    log.info("Complete — 11 stages, all_ok=%s  output: %s", all_ok, OUTPUT_DIR)
    return all_ok


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="PIXARTEK Stage Generator — Rostro Azul")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    log = setup_logging()
    log.info("PIXARTEK Stage Generator — Rostro Azul (Bidó, 1988)")
    sys.exit(0 if run(args.dry_run, log) else 1)


if __name__ == "__main__":
    main()
