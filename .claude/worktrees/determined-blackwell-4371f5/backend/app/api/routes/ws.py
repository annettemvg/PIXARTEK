"""WebSocket endpoint — pushes MQTT events to the frontend in real time."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
from app.mqtt.client import register_broadcast

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)

_connections: list[WebSocket] = []


async def _broadcast_to_ws(topic: str, payload: dict):
    dead = []
    for ws in _connections:
        try:
            await ws.send_text(json.dumps({"topic": topic, "payload": payload}))
        except Exception:
            dead.append(ws)
    for ws in dead:
        _connections.remove(ws)


# Register with MQTT client once at import time
register_broadcast(_broadcast_to_ws)


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    _connections.append(ws)
    logger.info(f"WS connected — total: {len(_connections)}")
    try:
        while True:
            # Keep connection alive; client can also send pings
            await ws.receive_text()
    except WebSocketDisconnect:
        _connections.remove(ws)
        logger.info(f"WS disconnected — total: {len(_connections)}")
