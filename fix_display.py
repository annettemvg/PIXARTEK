"""
Patch display.py to write source path directly to SOURCE_FILE
instead of compositing a PNG. The daemon handles all rendering.
"""

f = "/home/pi/pixartek/nodes/projection/display.py"
t = open(f, "rb").read().decode("utf-8-sig")

# Change DISPLAY_FILE to SOURCE_FILE
t = t.replace(
    'DISPLAY_FILE    = "/tmp/pixartek_display.png"',
    'DISPLAY_FILE    = "/tmp/pixartek_display.png"\nSOURCE_FILE     = "/tmp/pixartek_source.txt"'
)

# Replace the entire _render() function body with a simple path write
old_render = '''def _render() -> bool:
    if not _current_src:
        return False
    try:
        with _render_lock:
            with _state_lock:
                zoom = _zoom; ox = _offset_x; oy = _offset_y; ang = _angle

            with Image.open(_current_src) as img:
                img = img.convert("RGB")

                if ang != 0.0:
                    img = img.rotate(-ang, expand=True, resample=Image.BICUBIC)

                scale = zoom * min(DISPLAY_W / img.width, DISPLAY_H / img.height)
                tw = max(1, int(img.width  * scale))
                th = max(1, int(img.height * scale))
                scaled = img.resize((tw, th), Image.LANCZOS)

                bg = Image.new("RGB", (DISPLAY_W, DISPLAY_H), (255, 255, 255))
                x = (DISPLAY_W - tw) // 2 + ox
                y = (DISPLAY_H - th) // 2 + oy
                bg.paste(scaled, (x, y))

                # Atomic write: .tmp then rename so daemon never reads partial file
                tmp = DISPLAY_FILE + ".tmp"
                bg.save(tmp, "PNG")
                os.replace(tmp, DISPLAY_FILE)

        logger.info("Rendered zoom=%.2f angle=%.1f size=%dx%d pos=(%d,%d)", zoom, ang, tw, th, x, y)
        return True
    except Exception as e:
        logger.error("Render failed: %s", e)
        return False'''

new_render = '''def _render() -> bool:
    if not _current_src:
        return False
    try:
        # Write source path directly — daemon handles all rendering with correct aspect ratio
        with open(SOURCE_FILE, "w") as f:
            f.write(_current_src)
        logger.info("Queued for display: %s", _current_src)
        return True
    except Exception as e:
        logger.error("Render failed: %s", e)
        return False'''

if old_render in t:
    t = t.replace(old_render, new_render)
    open(f, "w").write(t)
    print("display.py patched — now writes source path directly")
else:
    print("Pattern not found, checking...")
    idx = t.find("def _render")
    print(repr(t[idx:idx+200]))
