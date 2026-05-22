"""
PIXARTEK — Loop de monitoreo de lienzo en tiempo real.

Captura frames continuamente desde el nodo de visión.
Detecta cambios con diferencia de píxeles (sin IA, rápido y gratis).
Cuando detecta actividad sostenida, llama a Gemini para análisis completo.
Envía el feedback de Pixi al frontend vía WebSocket.
"""
import asyncio
import logging
import time
from typing import Optional
import httpx
import numpy as np

log = logging.getLogger("monitor")

VISION_NODE_URL = "http://192.168.0.198:8000"

# Cuántos píxeles deben cambiar para considerar que hay actividad (0.0 - 1.0)
CHANGE_THRESHOLD = 0.02          # 2% del frame debe cambiar
# Segundos de actividad sostenida antes de llamar a Gemini
ACTIVITY_WINDOW = 10.0
# Segundos mínimos entre análisis de Gemini para no saturar la API
COOLDOWN_SECONDS = 90.0
# Intervalo entre capturas de frame (segundos)
CAPTURE_INTERVAL = 3.0

_state = {
    "active": False,
    "artwork_title": None,
    "artwork_artist": None,
    "stage_title": None,
    "stage_number": None,
    "last_analysis": 0.0,
    "activity_start": None,
    "prev_frame": None,
}

_broadcast_fn = None


def set_broadcast(fn):
    global _broadcast_fn
    _broadcast_fn = fn


async def _camera_power(on: bool):
    """Enciende o apaga la cámara del nodo de visión."""
    endpoint = "on" if on else "off"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{VISION_NODE_URL}/camera/{endpoint}")
        log.info("Camera %s", endpoint.upper())
    except Exception as e:
        log.warning("Camera power command failed: %s", e)


def start_session(artwork_title: str, artwork_artist: str, stage_title: str, stage_number: int):
    """Llamar cuando el estudiante empieza una sesión de pintura."""
    _state["active"] = True
    _state["artwork_title"] = artwork_title
    _state["artwork_artist"] = artwork_artist
    _state["stage_title"] = stage_title
    _state["stage_number"] = stage_number
    _state["last_analysis"] = 0.0
    _state["activity_start"] = None
    _state["prev_frame"] = None
    log.info(f"Monitor: sesión iniciada — {artwork_title} Etapa {stage_number}")
    import asyncio
    asyncio.create_task(_camera_power(True))


def update_stage(stage_title: str, stage_number: int):
    """Actualizar etapa cuando el estudiante avanza."""
    _state["stage_title"] = stage_title
    _state["stage_number"] = stage_number
    _state["last_analysis"] = 0.0
    _state["activity_start"] = None
    log.info(f"Monitor: etapa actualizada — Etapa {stage_number}: {stage_title}")


def stop_session():
    """Llamar cuando el estudiante termina la sesión."""
    _state["active"] = False
    _state["prev_frame"] = None
    log.info("Monitor: sesión detenida")
    import asyncio
    asyncio.create_task(_camera_power(False))


async def _capture_frame() -> Optional[bytes]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{VISION_NODE_URL}/capture")
            if res.status_code == 200 and res.content:
                return res.content
    except Exception as e:
        log.debug("Capture failed: %s", e)
    return None


async def _capture_frames(n: int = 8, interval: float = 0.5) -> list[bytes]:
    frames = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for _ in range(n):
            try:
                res = await client.get(f"{VISION_NODE_URL}/capture")
                if res.status_code == 200 and res.content:
                    frames.append(res.content)
            except Exception:
                pass
            await asyncio.sleep(interval)
    return frames


def _frame_changed(prev: bytes, curr: bytes) -> bool:
    """Compara dos frames JPEG. Retorna True si cambiaron suficientemente."""
    try:
        prev_arr = np.frombuffer(prev, dtype=np.uint8)
        curr_arr = np.frombuffer(curr, dtype=np.uint8)

        # Decodificar con numpy sin OpenCV — comparación simple de bytes
        # Normalizamos al mismo tamaño tomando el mínimo
        min_len = min(len(prev_arr), len(curr_arr))
        diff = np.abs(prev_arr[:min_len].astype(np.int16) - curr_arr[:min_len].astype(np.int16))
        changed_ratio = np.mean(diff > 10) / 1.0
        return changed_ratio > CHANGE_THRESHOLD
    except Exception:
        return False


async def _call_gemini_and_broadcast():
    """Captura 8 frames y llama a Gemini. Envía resultado al frontend."""
    from app.api.routes.chat import capture_frames, get_client, VISION_PROMPT
    from google.genai import types as genai_types

    if not _broadcast_fn:
        return

    artwork_title = _state["artwork_title"]
    stage_title = _state["stage_title"]
    stage_number = _state["stage_number"]
    artwork_artist = _state["artwork_artist"]

    log.info("Monitor: capturando 8 frames para análisis Gemini...")

    frames = await capture_frames(n=8, interval=0.5)
    if not frames:
        log.warning("Monitor: no se obtuvieron frames")
        return

    try:
        client = get_client()

        context = f"El estudiante está pintando '{artwork_title}'"
        if artwork_artist:
            context += f" de {artwork_artist}"
        if stage_title and stage_number:
            context += f", Etapa {stage_number}: {stage_title}"
        context += ". El sistema detectó actividad de pintura activa."

        prompt = context + f" Analiza esta secuencia de {len(frames)} fotogramas (cada 0.5s) y da feedback sobre técnica, trazos y agarre."

        parts = [genai_types.Part(text=prompt)]
        for frame in frames:
            parts.append(genai_types.Part(
                inline_data=genai_types.Blob(mime_type="image/jpeg", data=frame)
            ))

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[genai_types.Content(role="user", parts=parts)],
            config=genai_types.GenerateContentConfig(system_instruction=VISION_PROMPT),
        )

        reply = response.text
        log.info("Monitor: Gemini respondió — enviando al frontend")

        await _broadcast_fn("pixi/auto_feedback", {
            "reply": reply,
            "source": "monitor",
            "artwork_title": artwork_title,
            "stage_number": stage_number,
        })

    except Exception as e:
        log.error("Monitor: error Gemini — %s", e)


async def monitor_loop():
    """Loop principal. Corre como tarea asyncio en el background del backend."""
    log.info("Monitor: loop iniciado")

    while True:
        await asyncio.sleep(CAPTURE_INTERVAL)

        if not _state["active"]:
            continue

        frame = await _capture_frame()
        if frame is None:
            continue

        prev = _state["prev_frame"]
        _state["prev_frame"] = frame

        if prev is None:
            continue

        changed = _frame_changed(prev, frame)
        now = time.time()

        if changed:
            if _state["activity_start"] is None:
                _state["activity_start"] = now
                log.debug("Monitor: actividad detectada — iniciando ventana")

            elapsed = now - _state["activity_start"]
            since_last = now - _state["last_analysis"]

            if elapsed >= ACTIVITY_WINDOW and since_last >= COOLDOWN_SECONDS:
                _state["last_analysis"] = now
                _state["activity_start"] = None
                await _call_gemini_and_broadcast()
        else:
            # Sin cambio — resetear ventana de actividad
            _state["activity_start"] = None
