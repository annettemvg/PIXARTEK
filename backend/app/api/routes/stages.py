from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.artwork_stage import ArtworkStage
from app.models.artwork import Artwork
from app.mqtt.client import publish
from pathlib import Path
import os

router = APIRouter(prefix="/stages", tags=["stages"])

# stages.py lives at backend/app/api/routes/stages.py → project root is 5 levels up
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
FRONTEND_PUBLIC = PROJECT_ROOT / "frontend" / "public"


def _abs(path: str) -> str:
    """Return absolute path — resolve relative paths from project root."""
    p = Path(path)
    if p.is_absolute():
        # Paths like "/artworks/..." are relative to frontend/public on the server
        candidate = FRONTEND_PUBLIC / path.lstrip("/")
        if candidate.exists():
            return str(candidate)
        return str(p)
    return str(PROJECT_ROOT / p)


@router.get("/{artwork_id}")
async def get_stages(artwork_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ArtworkStage)
        .where(ArtworkStage.artwork_id == artwork_id)
        .order_by(ArtworkStage.stage_number)
    )
    stages = result.scalars().all()
    if not stages:
        raise HTTPException(status_code=404, detail="No stages found for this artwork")
    return [
        {
            "stage_id":              s.stage_id,
            "artwork_id":            s.artwork_id,
            "stage_number":          s.stage_number,
            "image_path":            s.image_path,
            "projection_image_path": s.projection_image_path,
            "created_at":            s.created_at.isoformat() if s.created_at else None,
        }
        for s in stages
    ]


@router.get("/{artwork_id}/{stage_number}/image")
async def get_stage_image(artwork_id: str, stage_number: int, db: AsyncSession = Depends(get_db)):
    # First try ArtworkStage table
    result = await db.execute(
        select(ArtworkStage)
        .where(ArtworkStage.artwork_id == artwork_id)
        .where(ArtworkStage.stage_number == stage_number)
    )
    stage = result.scalar_one_or_none()
    if stage:
        abs_path = _abs(stage.image_path)
        if os.path.exists(abs_path):
            return FileResponse(abs_path, media_type="image/png")

    # Fall back to Artwork JSON stages
    artwork = await db.get(Artwork, artwork_id)
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    stages = artwork.stages or []
    stage_data = next((s for s in stages if s.get("number") == stage_number), None)
    if not stage_data or "image" not in stage_data:
        raise HTTPException(status_code=404, detail=f"Stage {stage_number} not found")

    image_path = stage_data["image"]
    abs_path = _abs(image_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail=f"Stage image not found: {abs_path}")
    return FileResponse(abs_path, media_type="image/png")


@router.get("/{artwork_id}/{stage_number}/projection")
async def get_projection_image(artwork_id: str, stage_number: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ArtworkStage)
        .where(ArtworkStage.artwork_id == artwork_id)
        .where(ArtworkStage.stage_number == stage_number)
    )
    stage = result.scalar_one_or_none()
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    abs_path = _abs(stage.projection_image_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail=f"Projection image not found: {abs_path}")
    return FileResponse(abs_path, media_type="image/png")


@router.post("/{artwork_id}/{stage_number}/project")
async def trigger_projection(artwork_id: str, stage_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ArtworkStage)
        .where(ArtworkStage.artwork_id == artwork_id)
        .where(ArtworkStage.stage_number == stage_number)
    )
    stage = result.scalar_one_or_none()

    # Use the Host header if it has a real IP; otherwise fall back to MQTT host
    host = request.headers.get("host", "")
    if host.startswith("localhost") or host.startswith("127."):
        from app.core.config import settings
        host = f"{settings.mqtt_host}:8000"
    base_url = f"http://{host}"

    if not stage:
        # No artwork_stages record = no contour image exists. Clear the projector.
        publish("pixartek/projection/command", {
            "artwork_id": artwork_id,
            "stage":      stage_number,
            "image_path": "",
        })
        return {"ok": True, "stage": stage_number, "projected_url": None, "action": "clear"}

    proj_url = f"{base_url}/api/stages/{artwork_id}/{stage_number}/projection"
    publish("pixartek/projection/command", {
        "artwork_id":  artwork_id,
        "stage":       stage_number,
        "image_path":  proj_url,
        "image_url":   proj_url,
    })
    return {"ok": True, "stage": stage_number, "projected_url": proj_url}
