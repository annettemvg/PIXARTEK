"""
PIXARTEK — Nodo Visión (RPi4-A)
Servidor MJPEG + análisis de pintura en tiempo real.
Cámara siempre activa desde el inicio. Sin MQTT.

Endpoints:
  GET  /video_feed        — stream MJPEG en vivo
  GET  /capture           — foto fija JPEG
  GET  /status            — estado
  POST /reference         — establecer imagen de referencia
  GET  /feedback          — último resultado de análisis
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import time
import json
import logging
import threading
import uvicorn
from fastapi import FastAPI, Response, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

import pipeline
from config import (
    CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT,
    ANALYSIS_INTERVAL,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Pixartek-Vision")

app = FastAPI(title="Pixartek Vision Module")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Cámara ────────────────────────────────────────────────────────────────────

class CameraModule:
    def __init__(self):
        self.camera = None

    def init_cam(self):
        self.camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
        if self.camera.isOpened():
            logger.info("Camara inicializada correctamente (index=%d).", CAMERA_INDEX)
        else:
            logger.error("No se detecto camara en index %d.", CAMERA_INDEX)

    def _read(self):
        if self.camera is None or not self.camera.isOpened():
            self.init_cam()
            if not self.camera.isOpened():
                return None, None
        success, frame = self.camera.read()
        if not success:
            logger.warning("Fallo al leer frame — reiniciando camara.")
            self.camera.release()
            self.init_cam()
            return None, None
        return success, frame

    def get_frame(self) -> bytes | None:
        _, frame = self._read()
        if frame is None:
            return None
        ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return buffer.tobytes() if ret else None

    def get_raw_frame(self):
        _, frame = self._read()
        return frame


cam = CameraModule()

# ── Estado global ─────────────────────────────────────────────────────────────

_current_reference = {"artwork_id": None, "stage": None}
_last_feedback = None

# ── Loop de análisis ──────────────────────────────────────────────────────────

def _analysis_loop():
    logger.info("Loop de análisis iniciado (intervalo: %ds).", ANALYSIS_INTERVAL)
    while True:
        try:
            frame = cam.get_raw_frame()
            if frame is not None and pipeline._reference is not None:
                result = pipeline.analyze(frame)
                if result:
                    global _last_feedback
                    _last_feedback = {
                        "precision_pct":   result.precision_pct,
                        "color_deviation": result.color_deviation,
                        "stroke_errors":   [
                            {"zone": e.zone, "message": e.message}
                            for e in result.stroke_errors
                        ],
                        "suggestions":     result.suggestions,
                        "artwork_id":      _current_reference["artwork_id"],
                        "stage":           _current_reference["stage"],
                        "timestamp":       time.time(),
                    }
        except Exception as e:
            logger.error("Error en loop de análisis: %s", e)
        time.sleep(ANALYSIS_INTERVAL)


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    # Encender cámara inmediatamente al iniciar
    cam.init_cam()
    t = threading.Thread(target=_analysis_loop, daemon=True)
    t.start()
    logger.info("Vision node listo — camara activa.")


# ── Endpoints ─────────────────────────────────────────────────────────────────

def _frame_generator():
    while True:
        frame_bytes = cam.get_frame()
        if frame_bytes:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
        else:
            time.sleep(0.5)


@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(
        _frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/capture")
async def capture():
    frame_bytes = cam.get_frame()
    if frame_bytes:
        return Response(content=frame_bytes, media_type="image/jpeg")
    return Response(
        content='{"error":"Camara no disponible"}',
        status_code=503,
        media_type="application/json",
    )


@app.post("/camera/on")
async def camera_on():
    """Endpoint de compatibilidad — camara siempre activa."""
    if cam.camera is None or not cam.camera.isOpened():
        cam.init_cam()
    logger.info("camera/on recibido (camara ya activa)")
    return {"ok": True, "camera": "on"}


@app.post("/camera/off")
async def camera_off():
    """Endpoint de compatibilidad — ignorado, camara permanece activa."""
    logger.info("camera/off recibido — IGNORADO (camara siempre activa)")
    return {"ok": True, "camera": "on"}


@app.post("/reference")
async def set_reference(body: dict = Body(...)):
    artwork_id = body.get("artwork_id", "")
    stage      = body.get("stage", 0)
    image_path = body.get("image_path", "")
    ok = pipeline.set_reference(image_path, artwork_id, stage)
    if ok:
        _current_reference["artwork_id"] = artwork_id
        _current_reference["stage"]      = stage
        logger.info("Referencia activa: %s etapa %d", artwork_id, stage)
        return {"ok": True}
    else:
        logger.error("No se pudo cargar referencia: %s", image_path)
        return {"ok": False, "error": f"No se encontró: {image_path}"}


@app.get("/feedback")
async def get_feedback():
    if _last_feedback:
        return _last_feedback
    return {"ok": False, "error": "Sin feedback aún"}


@app.get("/status")
async def status():
    is_ok = cam.camera is not None and cam.camera.isOpened()
    return {
        "module":     "Pixartek-Vision",
        "online":     is_ok,
        "artwork_id": _current_reference["artwork_id"],
        "stage":      _current_reference["stage"],
        "analyzing":  pipeline._reference is not None,
        "timestamp":  time.time(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
