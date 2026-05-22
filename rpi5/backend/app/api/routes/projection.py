from fastapi import APIRouter
from pydantic import BaseModel
from app.mqtt.client import publish
from typing import Literal

router = APIRouter(prefix="/projection", tags=["projection"])

Action = Literal["up", "down", "left", "right", "zoom_in", "zoom_out", "rotate_left", "rotate_right", "reset"]


class AdjustRequest(BaseModel):
    action: Action


class AngleRequest(BaseModel):
    angle: float   # degrees, -180 to 180


@router.post("/adjust")
async def adjust_projection(body: AdjustRequest):
    publish("pixartek/projection/adjust", {"action": body.action})
    return {"ok": True, "action": body.action}


@router.post("/angle")
async def set_projection_angle(body: AngleRequest):
    publish("pixartek/projection/adjust", {"action": "set_angle", "angle": body.angle})
    return {"ok": True, "angle": body.angle}


class PresetRequest(BaseModel):
    name: str  # artwork_id, e.g. "flores-blancas"


@router.post("/preset/save")
async def save_preset(body: PresetRequest):
    publish("pixartek/projection/adjust", {"action": "save_preset", "name": body.name})
    return {"ok": True, "saved": body.name}


@router.post("/preset/load")
async def load_preset(body: PresetRequest):
    publish("pixartek/projection/adjust", {"action": "load_preset", "name": body.name})
    return {"ok": True, "loaded": body.name}
