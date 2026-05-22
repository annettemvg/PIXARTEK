from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.artwork import Artwork

router = APIRouter(prefix="/artworks", tags=["artworks"])


@router.get("")
async def list_artworks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Artwork))
    rows = result.scalars().all()
    return [_serialize(a) for a in rows]


@router.get("/{artwork_id}")
async def get_artwork(artwork_id: str, db: AsyncSession = Depends(get_db)):
    artwork = await db.get(Artwork, artwork_id)
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return _serialize(artwork)


def _serialize(a: Artwork) -> dict:
    return {
        "id": a.id, "title": a.title, "artist": a.artist, "year": a.year,
        "difficulty": a.difficulty, "duration_min": a.duration_min,
        "color": a.color, "image": a.image, "tags": a.tags, "stages": a.stages,
    }
