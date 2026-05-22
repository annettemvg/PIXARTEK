"""Mock vision node — simula el RPi4-B sirviendo frames del lienzo."""
import time
from fastapi import FastAPI
from fastapi.responses import Response
import httpx
import asyncio

app = FastAPI()

# Imagen de un lienzo real de prueba (pintura en progreso)
TEST_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/1280px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg"

_cached_image: bytes | None = None

async def get_test_image() -> bytes:
    global _cached_image
    if _cached_image is None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(TEST_IMAGE_URL)
            _cached_image = res.content
    return _cached_image

@app.get("/status")
def status():
    return {"module": "MockVision", "online": True, "timestamp": time.time()}

@app.get("/capture")
async def capture():
    img = await get_test_image()
    return Response(content=img, media_type="image/jpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
