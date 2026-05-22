"""
PIXARTEK — Nodo Visión (RPi4-A)
Servidor de video independiente. Emite el stream MJPEG en la red local
sin depender del master ni de MQTT.

Endpoints:
  GET /video_feed  — stream MJPEG en vivo (para navegador y la App)
  GET /capture     — foto fija JPEG (para análisis de IA)
  GET /status      — estado de la cámara
"""
import cv2
import time
import logging
import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Pixartek-Vision")

app = FastAPI(title="Pixartek Vision Module")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


class CameraModule:
    def __init__(self):
        self.camera = None
        self.reconnect_timeout = 5

    def _init_cam(self):
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 20)
        if self.camera.isOpened():
            logger.info("Camara inicializada correctamente.")
        else:
            logger.error("No se detecto ninguna camara en el puerto 0.")

    def get_frame(self) -> bytes | None:
        """Captura un frame y lo devuelve codificado en JPEG."""
        if self.camera is None or not self.camera.isOpened():
            self._init_cam()
            if not self.camera.isOpened():
                return None

        success, frame = self.camera.read()
        if not success:
            logger.warning("Fallo al leer frame. La camara se reiniciara en el siguiente intento.")
            self.camera.release()
            self.camera = None
            return None

        ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ret:
            return None
        return buffer.tobytes()


vision_module = CameraModule()


def frame_generator():
    """Generador continuo para el stream MJPEG."""
    while True:
        frame_bytes = vision_module.get_frame()
        if frame_bytes:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
        else:
            time.sleep(1)


@app.get("/video_feed")
async def video_feed():
    """Stream MJPEG en vivo. Abrir en navegador o usarlo como src en la App."""
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/capture")
async def capture():
    """Foto fija JPEG. Ideal para enviar a análisis de IA."""
    frame_bytes = vision_module.get_frame()
    if frame_bytes:
        return Response(content=frame_bytes, media_type="image/jpeg")
    return Response(content='{"error":"Camara no disponible"}', status_code=503, media_type="application/json")


@app.get("/status")
async def status():
    """Verifica si la cámara está respondiendo."""
    is_ok = vision_module.camera is not None and vision_module.camera.isOpened()
    return {
        "module": "Pixartek-Vision",
        "online": is_ok,
        "timestamp": time.time(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
