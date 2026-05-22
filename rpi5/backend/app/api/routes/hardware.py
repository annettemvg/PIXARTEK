import subprocess
import sys
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/hardware", tags=["hardware"])

COLORS_DIR = "/home/pi/pixartek/nodes/actuator/colors"

# Maps artwork_id → ciclo script path
CICLO_SCRIPTS: dict[str, str] = {
    "flores-blancas": f"{COLORS_DIR}/flores-blancas/ciclo_flores_blancas.py",
    "tucan-tropical":  f"{COLORS_DIR}/tucan-tropical/ciclo_tucan_tropical.py",
}

# Fallback actuator script
ACTUADOR_SCRIPT = os.getenv(
    "ACTUADOR_SCRIPT",
    "/home/pi/pixartek/nodes/actuator/actuador.py",
)

# Track the running subprocess so we don't double-fire
_actuador_proc: subprocess.Popen | None = None


def _actuador_running() -> bool:
    global _actuador_proc
    if _actuador_proc is None:
        return False
    if _actuador_proc.poll() is None:
        return True   # still running
    _actuador_proc = None
    return False


class DispenseRequest(BaseModel):
    pigment_slot: int = 1
    duration_ms: int = 500
    artwork_id: str = ""


@router.post("/dispense")
async def dispense(body: DispenseRequest):
    global _actuador_proc

    if _actuador_running():
        raise HTTPException(status_code=409, detail="Actuador ya en movimiento")

    # Pick the ciclo script for this artwork, or fall back to actuador.py
    script = CICLO_SCRIPTS.get(body.artwork_id, ACTUADOR_SCRIPT)

    if not os.path.exists(script):
        return {"ok": True, "simulated": True, "slot": body.pigment_slot, "script": script}

    try:
        _actuador_proc = subprocess.Popen(
            ["/usr/bin/python3", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=os.path.dirname(script),
        )
        return {"ok": True, "simulated": False, "pid": _actuador_proc.pid, "script": script}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al iniciar script: {e}")


@router.post("/dispense/stop")
async def dispense_stop():
    """Emergency stop — kills the actuator mid-cycle."""
    global _actuador_proc
    if _actuador_proc and _actuador_proc.poll() is None:
        _actuador_proc.terminate()
        try:
            _actuador_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _actuador_proc.kill()
        _actuador_proc = None
        return {"ok": True, "stopped": True}
    return {"ok": True, "stopped": False, "detail": "No estaba en movimiento"}


@router.post("/clean")
async def clean_brush():
    """Activate the water pump on the cleaning station RPi for 5 seconds."""
    import httpx
    CLEANING_URL = "http://192.168.0.149:8001/clean"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.post(CLEANING_URL)
            return res.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/status")
async def hardware_status():
    return {
        "actuador": "running" if _actuador_running() else "idle",
        "script": ACTUADOR_SCRIPT,
        "script_present": os.path.exists(ACTUADOR_SCRIPT),
    }


# ── Sequential pigment dispensing (no motor movement) ─────────────────────────

DISPENSE_SEQUENCES: dict[str, list[str]] = {
    "faro-nocturno": [
        "/home/pi/pixartek/nodes/actuator/colors/faro-nocturno/naranja.py",
        "/home/pi/pixartek/nodes/actuator/colors/faro-nocturno/indigo.py",
        "/home/pi/pixartek/nodes/actuator/colors/faro-nocturno/black.py",
        "/home/pi/pixartek/nodes/actuator/colors/faro-nocturno/amarillo_dorado.py",
    ],
    "flores-blancas": [
        "/home/pi/pixartek/nodes/actuator/colors/flores-blancas/burnt_sienna.py",
        "/home/pi/pixartek/nodes/actuator/colors/flores-blancas/champagne.py",
        "/home/pi/pixartek/nodes/actuator/colors/flores-blancas/lime_green.py",
        "/home/pi/pixartek/nodes/actuator/colors/flores-blancas/ivory_white.py",
    ],
    "mujer-sombrero": [
        "/home/pi/pixartek/nodes/actuator/colors/mujer-sombrero/azul.py",
        "/home/pi/pixartek/nodes/actuator/colors/mujer-sombrero/celeste.py",
        "/home/pi/pixartek/nodes/actuator/colors/mujer-sombrero/negro.py",
        "/home/pi/pixartek/nodes/actuator/colors/mujer-sombrero/verde.py",
        "/home/pi/pixartek/nodes/actuator/colors/mujer-sombrero/morado.py",
    ],
}

_sequence_running = False


class SequenceRequest(BaseModel):
    artwork_id: str


@router.post("/dispense/sequence")
async def dispense_sequence(body: SequenceRequest):
    global _sequence_running, _actuador_proc
    import asyncio

    if _sequence_running or _actuador_running():
        raise HTTPException(status_code=409, detail="Secuencia ya en progreso")

    # Si existe un ciclo script para esta obra, ejecutarlo directamente
    # (maneja motor + colores en las posiciones correctas)
    ciclo = CICLO_SCRIPTS.get(body.artwork_id)
    if ciclo:
        if not os.path.exists(ciclo):
            return {"ok": True, "simulated": True, "script": ciclo}
        try:
            _actuador_proc = subprocess.Popen(
                ["/usr/bin/python3", ciclo],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=os.path.dirname(ciclo),
            )
            return {"ok": True, "artwork_id": body.artwork_id, "total_colors": 4,
                    "script": os.path.basename(ciclo), "pid": _actuador_proc.pid}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al iniciar ciclo: {e}")

    # Sin ciclo script: ejecutar colores uno por uno (fallback)
    scripts = DISPENSE_SEQUENCES.get(body.artwork_id)
    if not scripts:
        raise HTTPException(status_code=404, detail="No hay secuencia para esta obra")

    async def run_sequence():
        global _sequence_running
        _sequence_running = True
        try:
            for i, script in enumerate(scripts):
                if not os.path.exists(script):
                    print(f"[SEQ] Script no encontrado (simulado): {script}")
                else:
                    proc = await asyncio.create_subprocess_exec(
                        "/usr/bin/python3", script,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                        cwd=os.path.dirname(script),
                    )
                    await proc.wait()
                    print(f"[SEQ] {os.path.basename(script)} completado")

                if i < len(scripts) - 1:
                    await asyncio.sleep(5)
        finally:
            _sequence_running = False

    asyncio.create_task(run_sequence())
    return {"ok": True, "artwork_id": body.artwork_id, "total_colors": len(scripts)}
