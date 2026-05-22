#!/usr/bin/env python3
"""
PIXARTEK Display Daemon
Watches /tmp/pixartek_source.txt for the current image path.
Loads and displays the original image directly — one step, no distortion.
"""
import os, sys, time, signal, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("display-daemon")

SOURCE_FILE = "/tmp/pixartek_source.txt"   # contains path to current image
POLL_MS     = 200

os.environ.setdefault("DISPLAY", ":0")
os.environ.setdefault("SDL_VIDEODRIVER", "x11")

import pygame

W, H = 1024, 768
_running = True

def shutdown(sig, frame):
    global _running
    log.info("Shutdown signal received")
    _running = False

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT,  shutdown)

pygame.init()
screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN | pygame.NOFRAME)
pygame.display.set_caption("PIXARTEK")
pygame.mouse.set_visible(False)
screen.fill((255, 255, 255))
pygame.display.flip()
log.info("Display daemon started %dx%d", W, H)

last_content = ""

def display_image(path):
    """Load image and scale with STRICT aspect ratio preservation."""
    try:
        img = pygame.image.load(path).convert()
        iw, ih = img.get_size()

        # Scale to fit screen keeping aspect ratio — never stretch
        scale = min(W / iw, H / ih)
        new_w = int(iw * scale)
        new_h = int(ih * scale)
        scaled = pygame.transform.smoothscale(img, (new_w, new_h))

        # Center on white background
        screen.fill((255, 255, 255))
        x = (W - new_w) // 2
        y = (H - new_h) // 2
        screen.blit(scaled, (x, y))
        pygame.display.flip()
        log.info("Displayed %s @ %dx%d -> %dx%d (scale=%.3f)", path, iw, ih, new_w, new_h, scale)
    except Exception as e:
        log.warning("Display error: %s", e)

while _running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            _running = False

    try:
        content = open(SOURCE_FILE).read().strip()
        if content != last_content and content and os.path.exists(content):
            last_content = content
            display_image(content)
    except FileNotFoundError:
        pass
    except Exception as e:
        log.warning("Read error: %s", e)

    pygame.time.wait(POLL_MS)

pygame.quit()
log.info("Display daemon stopped")
