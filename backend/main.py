"""PIXARTEK Backend — FastAPI entry point (RPi5 Nodo Principal)."""
import asyncio
import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import init_db, AsyncSessionLocal
from app.db.seed import seed_artworks
from app.mqtt.client import start_mqtt, stop_mqtt, set_event_loop
from app.api.routes import artworks, sessions, hardware, ws, config, stages, vision

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as db:
        await seed_artworks(db)
    set_event_loop(asyncio.get_event_loop())
    start_mqtt()
    yield
    stop_mqtt()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(artworks.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(hardware.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(stages.router, prefix="/api")
app.include_router(vision.router, prefix="/api")
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok", "node": "rpi5-main"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.api_host, port=settings.api_port, reload=settings.debug)
