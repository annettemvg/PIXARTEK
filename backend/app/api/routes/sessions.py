from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.base import get_db
from app.models.session import Session, SessionMetric
from app.models.artwork import Artwork
from app.mqtt.client import publish
import uuid, time, os

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Base path where artwork images live on the RPi nodes
ASSETS_PATH = os.getenv("ASSETS_PATH", "/home/pi/pixartek/assets/artwork")


class CreateSessionRequest(BaseModel):
    artwork_id: str
    start_stage: int = 1
    total_stages: int


class AdvanceStageRequest(BaseModel):
    stage: int


class RecordMetricRequest(BaseModel):
    stage: int
    precision_pct: float
    color_deviation: float
    elapsed_s: float
    feedback_json: dict = {}


@router.post("")
async def create_session(body: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    session = Session(
        id=str(uuid.uuid4()),
        artwork_id=body.artwork_id,
        current_stage=body.start_stage,
        total_stages=body.total_stages,
        started_at=time.time(),
        status="active",
    )
    db.add(session)
    await db.commit()

    # Trigger projection + vision analysis
    artwork = await db.get(Artwork, body.artwork_id)
    if artwork:
        await _publish_projection(session, artwork, body.start_stage, db)
        _publish_vision_reference(artwork, body.start_stage)

    return _serialize(session)


@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _serialize(session)


@router.patch("/{session_id}/stage")
async def advance_stage(session_id: str, body: AdvanceStageRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.current_stage = body.stage
    if body.stage > session.total_stages:
        session.status = "completed"
        session.ended_at = time.time()
    await db.commit()

    # Update projection with new stage
    artwork = await db.get(Artwork, session.artwork_id)
    if artwork and session.status != "completed":
        await _publish_projection(session, artwork, body.stage, db)
        _publish_vision_reference(artwork, body.stage)

    return _serialize(session)


@router.post("/{session_id}/metrics")
async def record_metric(session_id: str, body: RecordMetricRequest, db: AsyncSession = Depends(get_db)):
    metric = SessionMetric(
        session_id=session_id,
        stage=body.stage,
        precision_pct=body.precision_pct,
        color_deviation=body.color_deviation,
        elapsed_s=body.elapsed_s,
        feedback_json=body.feedback_json,
        recorded_at=time.time(),
    )
    db.add(metric)
    await db.commit()
    return {"ok": True}


@router.get("/{session_id}/metrics")
async def get_metrics(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SessionMetric).where(SessionMetric.session_id == session_id)
    )
    return [
        {"stage": m.stage, "precision_pct": m.precision_pct,
         "color_deviation": m.color_deviation, "elapsed_s": m.elapsed_s,
         "recorded_at": m.recorded_at}
        for m in result.scalars().all()
    ]


# ── MQTT helpers ──────────────────────────────────────────────────────────────

async def _publish_projection(session: Session, artwork: Artwork, stage: int, db: AsyncSession = None):
    """Publish projection/command so RPi4-A knows what to project."""
    from app.core.config import settings
    from app.models.artwork_stage import ArtworkStage
    stages = artwork.stages or []
    stage_data = next((s for s in stages if s.get("number") == stage), {})

    # Check if a contour (projection) image exists for this stage
    base_url = f"http://{settings.mqtt_host}:8000"
    has_proj = False
    if db is not None:
        result = await db.execute(
            select(ArtworkStage)
            .where(ArtworkStage.artwork_id == artwork.id)
            .where(ArtworkStage.stage_number == stage)
        )
        stage_obj = result.scalar_one_or_none()
        has_proj = stage_obj is not None and bool(stage_obj.projection_image_path)

    if not has_proj:
        # No contour image exists for this artwork stage — clear the projector.
        publish("pixartek/projection/command", {
            "artwork_id": artwork.id,
            "stage":      stage,
            "image_path": "",
        })
        return

    image_url = f"{base_url}/api/stages/{artwork.id}/{stage}/projection"
    payload = {
        "session_id":   session.id,
        "artwork_id":   artwork.id,
        "stage":        stage,
        "total_stages": session.total_stages,
        "image_path":   image_url,
        "image_url":    image_url,
        "stage_title":  stage_data.get("title", ""),
        "timestamp":    time.time(),
    }
    publish("pixartek/projection/command", payload)


def _publish_vision_reference(artwork: Artwork, stage: int):
    """Send reference image path to vision server for stage analysis."""
    stages = artwork.stages or []
    stage_data = next((s for s in stages if s.get("number") == stage), {})

    # Get the image path from the stage data
    ref_image = stage_data.get("image")
    if not ref_image:
        # Fallback to main artwork image
        ref_image = artwork.image

    # Build full path for the vision server
    if ref_image.startswith("/"):
        image_path = f"/home/pi/pixartek/frontend/public{ref_image}"
    else:
        image_path = f"/home/pi/pixartek/frontend/public/{ref_image}"

    publish("pixartek/vision/command", {
        "action": "set_reference",
        "artwork_id": artwork.id,
        "stage": stage,
        "image_path": image_path,
        "timestamp": time.time(),
    })


def _serialize(s: Session) -> dict:
    return {
        "id": s.id, "artwork_id": s.artwork_id,
        "current_stage": s.current_stage, "total_stages": s.total_stages,
        "started_at": s.started_at, "ended_at": s.ended_at, "status": s.status,
    }
