import os

MQTT_HOST   = os.getenv("MQTT_HOST",   "192.168.0.197")
MQTT_PORT   = int(os.getenv("MQTT_PORT", "1883"))
NODE_ID     = os.getenv("NODE_ID",     "rpi4-vision")
DEV_MODE    = os.getenv("DEV_MODE",    "true").lower() == "true"

# Camera
CAMERA_INDEX      = int(os.getenv("CAMERA_INDEX", "0"))   # cv2 index in dev
FRAME_WIDTH       = int(os.getenv("FRAME_WIDTH",  "1280"))
FRAME_HEIGHT      = int(os.getenv("FRAME_HEIGHT", "720"))
CAPTURE_FPS       = int(os.getenv("CAPTURE_FPS",  "5"))   # analysis rate

# Canvas ROI (normalized 0–1, set after calibration)
# These defaults assume camera roughly centered on canvas
CANVAS_ROI = {
    "x": float(os.getenv("CANVAS_ROI_X", "0.1")),
    "y": float(os.getenv("CANVAS_ROI_Y", "0.1")),
    "w": float(os.getenv("CANVAS_ROI_W", "0.8")),
    "h": float(os.getenv("CANVAS_ROI_H", "0.8")),
}

# Reference images (same folder as projection assets)
ASSETS_DIR  = os.getenv("ASSETS_DIR", "../../frontend/public/artworks")

HEARTBEAT_INTERVAL  = 5    # seconds
ANALYSIS_INTERVAL   = 2    # seconds between vision feedback publishes
RECONNECT_DELAY     = 3
