import os

MQTT_HOST     = os.getenv("MQTT_HOST",     "192.168.1.10")
MQTT_PORT     = int(os.getenv("MQTT_PORT", "1883"))
NODE_ID       = os.getenv("NODE_ID",       "rpi4-projection")
IMAGES_DIR    = os.getenv("IMAGES_DIR",    "/home/pi/pixartek/assets/artwork")
DEV_MODE      = os.getenv("DEV_MODE",      "true").lower() == "true"

# Display resolution (must match projector config in Settings)
DISPLAY_W     = int(os.getenv("DISPLAY_W", "1920"))
DISPLAY_H     = int(os.getenv("DISPLAY_H", "1080"))

HEARTBEAT_INTERVAL = 5   # seconds
RECONNECT_DELAY    = 3   # seconds between MQTT reconnect attempts
