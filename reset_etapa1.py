import json
path = "/home/pi/pixartek/presets/flores-blancas-1.json"
state = {"zoom": 1.0, "offset_x": 0, "offset_y": 0, "angle": 0.0}
open(path, "w").write(json.dumps(state))
print("Reset:", open(path).read())
