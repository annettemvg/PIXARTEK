"""PIXARTEK — TTS via Microsoft edge-tts (es-PR-KarinaNeural)."""
import asyncio
import tempfile
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter(prefix="/tts", tags=["tts"])

VOICE = "es-PR-KarinaNeural"  # Karina — Puerto Rican Spanish, natural feminine


class TTSRequest(BaseModel):
    text: str


@router.post("")
async def text_to_speech(req: TTSRequest):
    try:
        import edge_tts

        clean = req.text.strip()[:600]
        if not clean:
            raise HTTPException(status_code=400, detail="Empty text")

        communicate = edge_tts.Communicate(clean, VOICE, rate="+0%", pitch="+0Hz")

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name

        await communicate.save(tmp_path)

        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        os.unlink(tmp_path)
        return Response(content=audio_bytes, media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
