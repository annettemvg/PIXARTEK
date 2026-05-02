"""MQTT client for RPi5 — publishes commands, subscribes to feedback."""
import json
import asyncio
import logging
from paho.mqtt import client as mqtt

from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory registry of WebSocket broadcast callbacks
_broadcast_callbacks: list = []
_loop: asyncio.AbstractEventLoop | None = None


def register_broadcast(cb):
    _broadcast_callbacks.append(cb)


def set_event_loop(loop: asyncio.AbstractEventLoop):
    """Called at startup so MQTT thread can schedule coroutines on the main loop."""
    global _loop
    _loop = loop


def _broadcast(topic: str, payload: dict):
    if not _loop or not _broadcast_callbacks:
        return
    for cb in _broadcast_callbacks:
        asyncio.run_coroutine_threadsafe(cb(topic, payload), _loop)


def _on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("MQTT connected")
        client.subscribe("pixartek/#")
    else:
        logger.warning(f"MQTT connect failed rc={rc}")


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        logger.debug(f"MQTT rx {msg.topic}: {payload}")
        _broadcast(msg.topic, payload)
    except Exception as e:
        logger.error(f"MQTT message error: {e}")


_client: mqtt.Client | None = None


def get_mqtt() -> mqtt.Client:
    return _client


def start_mqtt():
    global _client
    _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    _client.on_connect = _on_connect
    _client.on_message = _on_message
    try:
        _client.connect(settings.mqtt_host, settings.mqtt_port, settings.mqtt_keepalive)
        _client.loop_start()
        logger.info(f"MQTT connecting to {settings.mqtt_host}:{settings.mqtt_port}")
    except Exception as e:
        logger.warning(f"MQTT unavailable (dev mode): {e}")


def stop_mqtt():
    if _client:
        _client.loop_stop()
        _client.disconnect()


def publish(topic: str, payload: dict):
    if _client and _client.is_connected():
        _client.publish(topic, json.dumps(payload))
