"""
Fix portrait projection: rotate display 90° and update dimensions.
"""
import subprocess, os

# 1. Rotate HDMI output 90° (right = clockwise)
env = dict(os.environ, DISPLAY=":0", XAUTHORITY="/var/run/lightdm/root/:0")
result = subprocess.run(
    ["xrandr", "--output", "HDMI-2", "--rotate", "right"],
    env=env, capture_output=True, text=True
)
print("xrandr:", result.returncode, result.stderr.strip() or "OK")

# 2. Update config.py: swap W and H
f = "/home/pi/pixartek/nodes/projection/config.py"
t = open(f).read()
t = t.replace("DISPLAY_W = 1024", "DISPLAY_W = 768")
t = t.replace("DISPLAY_H = 768",  "DISPLAY_H = 1024")
open(f, "w").write(t)
print("config.py updated: 768x1024 (portrait)")

# 3. Update display_daemon.py: swap W and H
f2 = "/home/pi/pixartek/nodes/projection/display_daemon.py"
t2 = open(f2).read()
t2 = t2.replace("W, H = 1024, 768", "W, H = 768, 1024")
open(f2, "w").write(t2)
print("display_daemon.py updated: 768x1024")

print("ALL DONE - restart services to apply")
