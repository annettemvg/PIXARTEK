f = "/home/pi/pixartek/nodes/projection/main.py"
t = open(f, "rb").read().decode("utf-8-sig")

old = '''    # Auto-load artwork preset if it exists
    import os as _os
    preset_path = f"/home/pi/pixartek/presets/{artwork_id}.json"
    if _os.path.exists(preset_path):
        display.load_preset(artwork_id)
        logger.info("Auto-loaded preset for %s", artwork_id)'''

new = '''    # Auto-load per-stage preset if it exists, else fall back to artwork preset
    import os as _os
    preset_key = f"{artwork_id}-{stage}"
    stage_preset  = f"/home/pi/pixartek/presets/{preset_key}.json"
    artwork_preset = f"/home/pi/pixartek/presets/{artwork_id}.json"
    if _os.path.exists(stage_preset):
        display.load_preset(preset_key)
        logger.info("Auto-loaded stage preset: %s", preset_key)
    elif _os.path.exists(artwork_preset):
        display.load_preset(artwork_id)
        logger.info("Auto-loaded artwork preset: %s", artwork_id)'''

if old in t:
    t = t.replace(old, new)
    open(f, "w").write(t)
    print("main.py updated - per-stage presets active")
else:
    print("Pattern not found - checking current content...")
    idx = t.find("Auto-load")
    print(repr(t[idx:idx+300]))
