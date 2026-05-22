import subprocess, os

# 1. Undo xrandr rotation
env = dict(os.environ, DISPLAY=":0", XAUTHORITY="/var/run/lightdm/root/:0")
subprocess.run(["xrandr", "--output", "HDMI-2", "--rotate", "normal"], env=env)
print("xrandr rotation: reset to normal")

# 2. Revert config.py
f = "/home/pi/pixartek/nodes/projection/config.py"
t = open(f).read()
t = t.replace("DISPLAY_W = 768",  "DISPLAY_W = 1024")
t = t.replace("DISPLAY_H = 1024", "DISPLAY_H = 768")
open(f, "w").write(t)
print("config.py: back to 1024x768")

# 3. Revert display_daemon.py
f2 = "/home/pi/pixartek/nodes/projection/display_daemon.py"
t2 = open(f2).read()
t2 = t2.replace("W, H = 768, 1024", "W, H = 1024, 768")
open(f2, "w").write(t2)
print("display_daemon.py: back to 1024x768")

# 4. Reset all flores-blancas presets to zero transforms
import json
presets_dir = "/home/pi/pixartek/presets"
state = {"zoom": 1.0, "offset_x": 0, "offset_y": 0, "angle": 0.0}
for i in [1, 2, 3]:
    path = f"{presets_dir}/flores-blancas-{i}.json"
    open(path, "w").write(json.dumps(state))
    print(f"Preset flores-blancas-{i}: reset to original")

print("ALL DONE")
