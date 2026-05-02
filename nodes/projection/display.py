"""
Display abstraction for the projection node.

  RPi (production):  uses `feh` — lightweight, no window decorations,
                     fullscreen over HDMI in Wayland/X11 kiosk mode.
  Dev (macOS/Linux): uses pygame — same fullscreen logic, easy to test.

Keep-alive strategy (prevents projector signal loss on static images):
  A background thread re-displays the current image every KEEPALIVE_INTERVAL
  seconds. This forces a new HDMI frame burst, preventing the projector from
  interpreting a long-static signal as "no source" and blanking.
  X11 DPMS and screensaver are also disabled at init time.
"""
import os
import subprocess
import threading
import time
import logging
from pathlib import Path

from config import DEV_MODE, DISPLAY_W, DISPLAY_H

logger = logging.getLogger(__name__)

KEEPALIVE_INTERVAL = 300   # re-display every 5 minutes

_pg_screen   = None        # pygame surface (dev mode)
_feh_proc    = None        # running feh process (RPi)
_current_path: str | None = None   # path of image currently on screen
_keepalive_thread: threading.Thread | None = None
_running = True


# ── Public API ────────────────────────────────────────────────────────────────

def init():
    """Initialize display backend and start keep-alive thread."""
    global _keepalive_thread, _running
    _running = True

    _disable_dpms()

    if DEV_MODE:
        _init_pygame()
    else:
        logger.info("RPi display mode — feh will be used per command")

    _keepalive_thread = threading.Thread(target=_keepalive_loop, daemon=True)
    _keepalive_thread.start()
    logger.info("Keep-alive thread started (interval=%ds)", KEEPALIVE_INTERVAL)


def show(image_path: str) -> bool:
    """Display image_path fullscreen. Returns True on success."""
    global _current_path
    path = Path(image_path)
    if not path.exists():
        logger.error("Image not found: %s", image_path)
        return False

    success = _show_pygame(str(path)) if DEV_MODE else _show_feh(str(path))
    if success:
        _current_path = str(path)
    return success


def clear():
    """Black out the display."""
    global _current_path
    _current_path = None
    if DEV_MODE:
        _clear_pygame()
    else:
        _kill_feh()


def shutdown():
    """Release display resources."""
    global _running
    _running = False
    if DEV_MODE:
        _quit_pygame()
    else:
        _kill_feh()


# ── Keep-alive loop ───────────────────────────────────────────────────────────

def _keepalive_loop():
    """
    Re-display the current image on a timer.
    Prevents the projector from losing HDMI signal on long static frames.
    """
    while _running:
        time.sleep(KEEPALIVE_INTERVAL)
        if _current_path and _running:
            logger.info("Keep-alive: refreshing %s", _current_path)
            if DEV_MODE:
                _show_pygame(_current_path)
            else:
                _show_feh(_current_path)


# ── DPMS / screensaver disable ────────────────────────────────────────────────

def _disable_dpms():
    """
    Disable X11 DPMS and screensaver so the display never blanks.
    Safe to call even if X11 is not running (errors are swallowed).
    """
    cmds = [
        ["xset", "-dpms"],          # disable DPMS (energy star)
        ["xset", "s", "off"],       # disable screensaver
        ["xset", "s", "noblank"],   # prevent screen blanking
    ]
    env = {**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}
    for cmd in cmds:
        try:
            subprocess.run(cmd, env=env, capture_output=True, timeout=5)
            logger.info("ran: %s", " ".join(cmd))
        except Exception as e:
            logger.debug("xset not available (%s) — skipping", e)


# ── pygame (dev) ──────────────────────────────────────────────────────────────

def _init_pygame():
    global _pg_screen
    try:
        import pygame
        pygame.init()
        pygame.display.set_caption("PIXARTEK — Proyección")
        _pg_screen = pygame.display.set_mode(
            (DISPLAY_W, DISPLAY_H),
            pygame.RESIZABLE
        )
        _pg_screen.fill((0, 0, 0))
        pygame.display.flip()
        logger.info("pygame display %d×%d ready", DISPLAY_W, DISPLAY_H)
    except ImportError:
        logger.warning("pygame not installed — display simulated")


def _show_pygame(path: str) -> bool:
    global _pg_screen
    try:
        import pygame
    except ImportError:
        logger.info("[SIMULATED] Would project: %s", path)
        return True

    try:
        if _pg_screen is None:
            logger.info("[SIMULATED] Would project: %s", path)
            return True
        img = pygame.image.load(path)
        img = pygame.transform.scale(img, (DISPLAY_W, DISPLAY_H))
        _pg_screen.blit(img, (0, 0))
        pygame.display.flip()
        pygame.event.pump()
        return True
    except Exception as e:
        logger.error("pygame display error: %s", e)
        return False


def _clear_pygame():
    try:
        import pygame
        if _pg_screen:
            _pg_screen.fill((0, 0, 0))
            pygame.display.flip()
    except Exception:
        pass


def _quit_pygame():
    try:
        import pygame
        pygame.quit()
    except Exception:
        pass


# ── feh / fbi (RPi production) ───────────────────────────────────────────────

def _show_feh(path: str) -> bool:
    """Try feh (needs DISPLAY), fallback to fbi (framebuffer)."""
    global _feh_proc
    _kill_feh()

    if os.environ.get("DISPLAY"):
        try:
            _feh_proc = subprocess.Popen(
                [
                    "feh",
                    "--fullscreen",
                    "--hide-pointer",
                    "-Z",
                    "--no-xinerama",
                    "--no-rotate",
                    path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("feh: projecting %s (pid %d)", path, _feh_proc.pid)
            return True
        except FileNotFoundError:
            logger.warning("feh not found — trying fbi")
        except Exception as e:
            logger.warning("feh error: %s — trying fbi", e)

    for cmd in ["fbi", "fim"]:
        try:
            _feh_proc = subprocess.Popen(
                [cmd, "-T", "1", "-noverbose", "-a", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("%s: projecting %s (pid %d)", cmd, path, _feh_proc.pid)
            return True
        except FileNotFoundError:
            continue
        except Exception as e:
            logger.error("%s error: %s", cmd, e)

    logger.error("No display backend available. Install with: sudo apt install feh")
    return False


def _kill_feh():
    global _feh_proc
    if _feh_proc and _feh_proc.poll() is None:
        _feh_proc.terminate()
        try:
            _feh_proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            _feh_proc.kill()
    _feh_proc = None
