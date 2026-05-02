"""
PIXARTEK — Nodo Visión (RPi4-B)

Suscribe a:  pixartek/vision/calibrate
             pixartek/projection/command   (para cargar referencia de etapa)
Publica en:  pixartek/vision/feedback
             pixartek/vision/metrics
             pixartek/system/heartbeat
"""
import json
import time
import signal
import logging
import threading

from paho.mqtt import client as mqtt

import config
import camera
import calibration
import pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── State ─────────────────────────────────────────────────────────────────────
_running        = True
_session_id:  str | None = None
_current_artwork: str    = ""
_current_stage:   int    = 0
_mqtt_client: mqtt.Client | None = None


# ── MQTT callbacks ────────────────────────────────────────────────────────────

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"Connected to MQTT {config.MQTT_HOST}:{config.MQTT_PORT}")
        client.subscribe("pixartek/vision/calibrate")
        client.subscribe("pixartek/projection/command")
        _publish_heartbeat(client)
    else:
        logger.warning(f"MQTT connect failed rc={rc}")


def on_disconnect(client, userdata, rc, properties=None, reasoncode=None):
    logger.warning(f"MQTT disconnected rc={rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        logger.debug(f"RX {msg.topic}")

        if msg.topic == "pixartek/vision/calibrate":
            _handle_calibrate(client, payload)

        elif msg.topic == "pixartek/projection/command":
            _handle_projection_command(payload)

    except json.JSONDecodeError:
        logger.error(f"Invalid JSON on {msg.topic}")
    except Exception as e:
        logger.error(f"on_message error: {e}")


# ── Command handlers ──────────────────────────────────────────────────────────

def _handle_calibrate(client: mqtt.Client, payload: dict):
    """
    Full calibration sequence:
      1. Capture a frame
      2. Perspective calibration (homography)
      3. Color calibration (reference card)
    """
    logger.info("Starting calibration sequence...")
    frame = camera.read()
    if frame is None:
        logger.error("Calibration failed: no frame")
        return

    corners = payload.get("canvas_corners")   # optional manual corners
    cal_ok  = calibration.calibrate_perspective(frame, corners)
    col_ok  = calibration.calibrate_color(frame)

    result = {
        "node":         config.NODE_ID,
        "perspective":  cal_ok,
        "color":        col_ok,
        "color_scale":  calibration.get_color_scale().tolist(),
        "timestamp":    time.time(),
    }
    client.publish("pixartek/vision/calibrate", json.dumps(result))
    logger.info(f"Calibration complete: perspective={cal_ok} color={col_ok}")


def _handle_projection_command(payload: dict):
    """When a new stage is projected, load the matching reference image."""
    global _current_artwork, _current_stage, _session_id

    artwork_id = payload.get("artwork_id", "")
    stage      = payload.get("stage", 0)
    image_path = payload.get("image_path", "")
    _session_id = payload.get("session_id")

    if not image_path:
        logger.warning("projection/command missing image_path")
        return

    ok = pipeline.set_reference(image_path, artwork_id, stage)
    if ok:
        _current_artwork = artwork_id
        _current_stage   = stage
        logger.info(f"Reference updated: {artwork_id} stage {stage}")


# ── Analysis loop ─────────────────────────────────────────────────────────────

def _analysis_loop(client: mqtt.Client):
    """Capture frames and publish feedback at ANALYSIS_INTERVAL."""
    while _running:
        time.sleep(config.ANALYSIS_INTERVAL)

        frame = camera.read()
        if frame is None:
            logger.warning("analysis_loop: camera returned None")
            continue

        # Publish camera frame as JPEG for live display ALWAYS (even without active session)
        _publish_camera_frame(client, frame)

        # Only analyze and publish feedback if there's an active session
        if not _current_artwork:
            continue   # no active session yet

        result = pipeline.analyze(frame)
        if result is None:
            continue

        # Publish feedback
        feedback = {
            "node":            config.NODE_ID,
            "artwork_id":      _current_artwork,
            "stage":           _current_stage,
            "precision_pct":   result.precision_pct,
            "color_deviation": result.color_deviation,
            "stroke_errors":   [{"zone": e.zone, "message": e.message}
                                 for e in result.stroke_errors],
            "suggestions":     result.suggestions,
            "timestamp":       time.time(),
        }
        client.publish("pixartek/vision/feedback", json.dumps(feedback))

        # Publish metrics
        metrics = {
            "node":          config.NODE_ID,
            "session_id":    _session_id,
            "stage":         _current_stage,
            "precision_pct": result.precision_pct,
            "timestamp":     time.time(),
        }
        client.publish("pixartek/vision/metrics", json.dumps(metrics))

        logger.info(
            f"Feedback published: precision={result.precision_pct}% "
            f"ΔE={result.color_deviation} errors={len(result.stroke_errors)}"
        )


def _publish_camera_frame(client: mqtt.Client, frame: "numpy.ndarray"):
    """Publish the current camera frame as JPEG for live display in frontend."""
    try:
        import cv2
        import io

        # Encode frame as JPEG
        success, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if success:
            jpeg_bytes = jpeg.tobytes()
            client.publish("pixartek/vision/camera-frame", jpeg_bytes)
    except ImportError:
        # Fallback using PIL if cv2 not available
        try:
            from PIL import Image
            import io
            img = Image.fromarray(frame[:, :, ::-1])  # BGR to RGB
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=80)
            jpeg_bytes = buffer.getvalue()
            client.publish("pixartek/vision/camera-frame", jpeg_bytes)
        except Exception as e:
            logger.debug(f"Failed to publish camera frame: {e}")
    except Exception as e:
        logger.debug(f"Failed to encode camera frame: {e}")


# ── Heartbeat ─────────────────────────────────────────────────────────────────

def _heartbeat_loop(client: mqtt.Client):
    while _running:
        _publish_heartbeat(client)
        time.sleep(config.HEARTBEAT_INTERVAL)


def _publish_heartbeat(client: mqtt.Client):
    try:
        client.publish("pixartek/system/heartbeat", json.dumps({
            "node":      config.NODE_ID,
            "status":    "ok",
            "timestamp": time.time(),
        }))
    except Exception as e:
        logger.warning(f"Heartbeat error: {e}")


# ── Graceful shutdown ─────────────────────────────────────────────────────────

def _shutdown(signum, frame):
    global _running
    logger.info("Shutting down vision node...")
    _running = False
    camera.release()
    if _mqtt_client:
        _mqtt_client.disconnect()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    global _mqtt_client

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info(f"PIXARTEK Vision Node starting — DEV_MODE={config.DEV_MODE}")

    if not camera.init():
        logger.error("Camera init failed — continuing in mock mode")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=config.NODE_ID)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message
    _mqtt_client = client

    # Connect to MQTT
    try:
        client.connect(config.MQTT_HOST, config.MQTT_PORT, keepalive=60)
        client.loop_start()  # Start non-blocking loop for multiple threads
        logger.info("MQTT client loop started")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT: {e}")
        return

    # Background threads
    threading.Thread(target=_heartbeat_loop, args=(client,), daemon=True).start()
    threading.Thread(target=_analysis_loop,  args=(client,), daemon=True).start()

    # Keep main thread alive
    while _running:
        time.sleep(1)

    logger.info("Vision node stopped.")


if __name__ == "__main__":
    main()
