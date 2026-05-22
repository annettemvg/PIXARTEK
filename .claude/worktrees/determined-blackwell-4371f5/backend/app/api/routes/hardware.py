from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/hardware", tags=["hardware"])

# On RPi this imports GPIO. In dev we mock it.
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False


class DispenseRequest(BaseModel):
    pigment_slot: int = 1   # 1–N pumps
    duration_ms: int = 500


@router.post("/dispense")
async def dispense(body: DispenseRequest):
    if HAS_GPIO:
        # TODO: pulse GPIO pin for the given pump slot
        pass
    return {"ok": True, "simulated": not HAS_GPIO, "slot": body.pigment_slot, "duration_ms": body.duration_ms}


@router.post("/clean")
async def clean_brush():
    if HAS_GPIO:
        # TODO: trigger IR-based clean cycle
        pass
    return {"ok": True, "simulated": not HAS_GPIO}


@router.get("/status")
async def hardware_status():
    return {
        "gpio_available": HAS_GPIO,
        "actuator": "idle",
        "pumps": [{"slot": i, "state": "idle"} for i in range(1, 5)],
    }
