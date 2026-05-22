"""PIXARTEK MQTT topic constants — single source of truth for all nodes."""

PROJECTION_COMMAND  = "pixartek/projection/command"
PROJECTION_STATUS   = "pixartek/projection/status"

VISION_FEEDBACK     = "pixartek/vision/feedback"
VISION_CALIBRATE    = "pixartek/vision/calibrate"
VISION_METRICS      = "pixartek/vision/metrics"

HARDWARE_DISPENSE   = "pixartek/hardware/dispense"
HARDWARE_STATUS     = "pixartek/hardware/status"

SYSTEM_HEARTBEAT    = "pixartek/system/heartbeat"


# Node identifiers
NODE_MAIN       = "rpi5-main"
NODE_PROJECTION = "rpi4-projection"
NODE_VISION     = "rpi4-vision"

HEARTBEAT_INTERVAL_S = 5
