import json
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/config", tags=["config"])

CONFIG_FILE = Path(__file__).parent.parent.parent.parent / "pixartek_config.json"

DEFAULTS = {
    "mqttHost": "192.168.86.243", "mqttPort": 1883,
    "rpi5Ip": "192.168.86.243", "rpi4aIp": "192.168.86.244", "rpi4bIp": "192.168.86.245",
    "projectionWidth": 1920, "projectionHeight": 1080, "projectionBrightness": 80,
    "audioEnabled": True, "audioVolume": 70,
    "kioskMode": True, "language": "es",
    "autoAdvanceStage": False, "autoAdvanceThreshold": 90,
}


def _load() -> dict:
    if CONFIG_FILE.exists():
        return {**DEFAULTS, **json.loads(CONFIG_FILE.read_text())}
    return DEFAULTS.copy()


def _save(data: dict):
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


@router.get("")
async def get_config():
    return _load()


@router.put("")
async def update_config(body: dict):
    current = _load()
    current.update(body)
    _save(current)
    return current
