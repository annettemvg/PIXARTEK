"""
PIXARTEK — Nodo Proyección (RPi4-A)

Suscribe a:  pixartek/projection/command
Publica en:  pixartek/projection/status
             pixartek/system/heartbeat
"""
import json
import time
import signal
import logging
import threading
import urllib.request

from paho.mqtt import client as mqtt

import config
import display

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── State ─────────────────────────────────────────────────────────────────────
_running        = True
_current_artwork: str | None = None
_current_stage:   int        = 0
_mqtt_client:     mqtt.Client | None = None


# ── MQTT callbacks ────────────────────────────────────────────────────────────

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"Connected to MQTT broker {config.MQTT_HOST}:{config.MQTT_PORT}")
        client.subscribe("pixartek/projection/command")
        client.subscribe("pixartek/system/heartbeat")
        _publish_status(client, active=False)
    else:
        logger.warning(f"MQTT connect failed — rc={rc}")


def on_disconnect(client, userdata, rc, properties=None, reasoncode=None):
    logger.warning(f"MQTT disconnected (rc={rc}) — will reconnect in {config.RECONNECT_DELAY}s")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        logger.info(f"RX {msg.topic}: {payload}")

        if msg.topic == "pixartek/projection/command":
            _handle_projection_command(client, payload)

    except json.JSONDecodeError:
        logger.error(f"Invalid JSON on {msg.topic}")
    except Exception as e:
        logger.error(f"on_message error: {e}")


# ── Command handler ───────────────────────────────────────────────────────────

def _handle_projection_command(client: mqtt.Client, payload: dict):
    global _current_artwork, _current_stage

    artwork_id  = payload.get("artwork_id", "")
    stage       = payload.get("stage", 0)
    image_path  = payload.get("image_path", "")

    logger.info(f"Projecting artwork={artwork_id} stage={stage} image={image_path}")

    # Support HTTP URLs — download to /tmp before displaying
    if image_path.startswith("http://") or image_path.startswith("https://"):
        tmp_path = f"/tmp/pixartek_proj_{artwork_id}_{stage}.png"
        try:
            urllib.request.urlretrieve(image_path, tmp_path)
            logger.info(f"Downloaded projection image to {tmp_path}")
            image_path = tmp_path
        except Exception as e:
            logger.error(f"Failed to download projection image: {e}")
            _publish_status(client, active=False, artwork_id=artwork_id, stage=stage)
            return

    success = display.show(image_path)

    _current_artwork = artwork_id
    _current_stage   = stage

    _publish_status(client, active=success, artwork_id=artwork_id, stage=stage)


# ── Publishers ────────────────────────────────────────────────────────────────

def _publish_status(client: mqtt.Client, active: bool,
                    artwork_id: str = "", stage: int = 0):
    payload = {
        "node":       config.NODE_ID,
        "active":     active,
        "artwork_id": artwork_id,
        "stage":      stage,
        "timestamp":  time.time(),
    }
    client.publish("pixartek/projection/status", json.dumps(payload))
    logger.info(f"TX projection/status: active={active}")


def _heartbeat_loop(client: mqtt.Client):
    while _running:
        payload = {
            "node":      config.NODE_ID,
            "status":    "ok",
            "timestamp": time.time(),
        }
        try:
            client.publish("pixartek/system/heartbeat", json.dumps(payload))
        except Exception as e:
            logger.warning(f"Heartbeat publish failed: {e}")
        time.sleep(config.HEARTBEAT_INTERVAL)


# ── Graceful shutdown ─────────────────────────────────────────────────────────

def _shutdown(signum, frame):
    global _running
    logger.info("Shutting down projection node...")
    _running = False
    display.clear()
    display.shutdown()
    if _mqtt_client:
        _mqtt_client.disconnect()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    global _mqtt_client

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info(f"PIXARTEK Projection Node starting — DEV_MODE={config.DEV_MODE}")
    display.init()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=config.NODE_ID)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message
    _mqtt_client = client

    # Heartbeat thread
    hb = threading.Thread(target=_heartbeat_loop, args=(client,), daemon=True)

    # Connect with auto-reconnect
    while _running:
        try:
            client.connect(config.MQTT_HOST, config.MQTT_PORT, keepalive=60)
            hb.start()
            client.loop_forever(retry_first_connection=True)
            break
        except Exception as e:
            logger.error(f"MQTT connection error: {e} — retrying in {config.RECONNECT_DELAY}s")
            time.sleep(config.RECONNECT_DELAY)

    logger.info("Projection node stopped.")


if __name__ == "__main__":
    main()
