"""Vision Node endpoints — proxy al servidor de video independiente en RPi4-A."""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["vision"])

VISION_BASE = f"http://{settings.rpi4a_ip}:8000"


@router.get("/camera-frame")
async def get_camera_frame():
    """Redirige al endpoint /capture del nodo de visión independiente."""
    return RedirectResponse(url=f"{VISION_BASE}/capture")


@router.get("/status")
async def vision_status():
    """Redirige al /status del nodo de visión independiente."""
    return RedirectResponse(url=f"{VISION_BASE}/status")
