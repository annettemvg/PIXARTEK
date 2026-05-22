"""
Patches display.py and main.py on RPi4 to support artwork presets.
Run with: python3 patch_presets.py
"""
import os, json

# ── 1. Patch display.py ──────────────────────────────────────────────────────
DISPLAY = "/home/pi/pixartek/nodes/projection/display.py"
t = open(DISPLAY, "rb").read().decode("utf-8-sig")

PRESET_CODE = '''

PRESET_DIR = "/home/pi/pixartek/presets"

def save_preset(name: str) -> dict:
    """Save current state as a named preset."""
    os.makedirs(PRESET_DIR, exist_ok=True)
    state = get_state()
    path = os.path.join(PRESET_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(state, f)
    logger.info("Saved preset '%s': %s", name, state)
    return state

def load_preset(name: str) -> bool:
    """Load a named preset and re-render."""
    global _zoom, _offset_x, _offset_y, _angle
    path = os.path.join(PRESET_DIR, f"{name}.json")
    if not os.path.exists(path):
        logger.warning("Preset '%s' not found", name)
        return False
    with open(path) as f:
        state = json.load(f)
    with _state_lock:
        _zoom     = state.get("zoom", 1.0)
        _offset_x = state.get("offset_x", 0)
        _offset_y = state.get("offset_y", 0)
        _angle    = state.get("angle", 0.0)
    logger.info("Loaded preset '%s': %s", name, state)
    if _current_src:
        _render()
    return True
'''

# Add json import if not present
if "import json" not in t:
    t = t.replace("import os, subprocess", "import json\nimport os, subprocess")
elif "import os, subprocess" in t and "import json" not in t:
    t = t.replace("import os, subprocess", "import json\nimport os, subprocess")

# Add preset functions before _keepalive_loop
if "def save_preset" not in t:
    t = t.replace("def _keepalive_loop", PRESET_CODE + "\ndef _keepalive_loop")

open(DISPLAY, "w").write(t)
print("display.py patched")

# ── 2. Patch main.py ─────────────────────────────────────────────────────────
MAIN = "/home/pi/pixartek/nodes/projection/main.py"
t2 = open(MAIN, "rb").read().decode("utf-8-sig")

# Add save_preset / load_preset handling inside _handle_adjust
OLD_ADJUST = '''def _handle_adjust(client, payload):
    action = payload.get("action", "")
    if not action:
        return
    state = display.adjust(action, angle=payload.get("angle"))'''

NEW_ADJUST = '''def _handle_adjust(client, payload):
    action = payload.get("action", "")
    if not action:
        return

    # Preset commands
    if action == "save_preset":
        name = payload.get("name", "default")
        state = display.save_preset(name)
        logger.info("Preset saved: %s = %s", name, state)
        client.publish("pixartek/projection/state", __import__("json").dumps({
            "node": config.NODE_ID, "preset_saved": name, **state,
            "timestamp": __import__("time").time(),
        }))
        return
    if action == "load_preset":
        name = payload.get("name", "default")
        display.load_preset(name)
        return

    state = display.adjust(action, angle=payload.get("angle"))'''

if "save_preset" not in t2:
    t2 = t2.replace(OLD_ADJUST, NEW_ADJUST)

# Auto-load preset when projecting
OLD_PROJECT = '''    success = display.show(image_path)
    _current_artwork = artwork_id
    _current_stage   = stage'''

NEW_PROJECT = '''    # Auto-load artwork preset if it exists
    import os as _os
    preset_path = f"/home/pi/pixartek/presets/{artwork_id}.json"
    if _os.path.exists(preset_path):
        display.load_preset(artwork_id)
        logger.info("Auto-loaded preset for %s", artwork_id)

    success = display.show(image_path)
    _current_artwork = artwork_id
    _current_stage   = stage'''

if "Auto-load artwork preset" not in t2:
    t2 = t2.replace(OLD_PROJECT, NEW_PROJECT)

open(MAIN, "w").write(t2)
print("main.py patched")

# ── 3. Create presets directory ───────────────────────────────────────────────
os.makedirs("/home/pi/pixartek/presets", exist_ok=True)
print("presets/ dir created")
print("ALL DONE")
