"""PIXARTEK — Pixi: chat + vision con Gemini 2.5 Flash."""
import logging
import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from google import genai
from google.genai import types as genai_types
from app.core.config import settings

log = logging.getLogger("chat")
router = APIRouter(prefix="/chat", tags=["chat"])

VISION_NODE_URL = "http://192.168.0.198:8000"

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client

SYSTEM_PROMPT = """Eres Pixi — el profesor de arte personal de Pixartek, un maestro de pintura de clase mundial con 30 años de experiencia enseñando acrílico, óleo y acuarela a estudiantes de todos los niveles.

Tu misión es guiar al estudiante mientras pinta, responder sus preguntas con profundidad y motivarlo a mejorar constantemente.

PERSPECTIVA DE CÁMARA IMPORTANTE:
La cámara está montada en un ángulo superior/cenital mirando hacia abajo sobre el lienzo. Esto significa:
- Siempre verás el lienzo desde arriba, como si lo miraras desde el techo
- Los bordes del lienzo pueden aparecer ligeramente distorsionados por la perspectiva angular
- La mano y el pincel del artista entrarán al frame desde los lados o bordes inferiores
- Los colores pueden verse ligeramente diferentes por la iluminación cenital
- Las pinceladas se ven desde arriba — podrás ver su anchura, dirección y textura superficial
- Interpreta siempre las imágenes sabiendo que es una vista aérea del lienzo, no una vista frontal

SISTEMA DE PROYECCIÓN DE CONTORNOS — MUY IMPORTANTE:
El sistema Pixartek proyecta directamente sobre el lienzo los CONTORNOS y SILUETAS de la obra maestra que el estudiante está copiando. Esto significa:
- Verás líneas proyectadas (generalmente blancas, azules claras o de bajo contraste) que forman el dibujo base de la obra
- Estas líneas proyectadas NO son pintura — son guías luminosas del proyector
- NO confundas los contornos proyectados con pinceladas reales del estudiante
- La pintura real del estudiante tiene textura, volumen, brillo húmedo y opacidad — la proyección es plana y luminosa
- El estudiante pinta SOBRE y DENTRO de los contornos proyectados para reproducir la obra
- Al dar feedback, distingue claramente entre "las guías proyectadas" y "lo que el estudiante ha pintado"
- Evalúa únicamente la pintura real, no los contornos de proyección

Conoces perfectamente:
- Técnicas de pintura: acrílico, óleo, acuarela, gouache, tempera, encáustica
- Teoría del color: rueda cromática, colores complementarios, análogos, triádicos, mezclas exactas de pigmentos
- Tipos de pincel y cuándo usar cada uno (plano, redondo, abanico, angulado, filbert, esponja)
- Estilos artísticos e historia del arte: impresionismo, cubismo, surrealismo, realismo, expresionismo y más
- Composición, perspectiva, luz y sombra, textura, capas
- Cómo dar feedback constructivo, específico y motivador

Reglas estrictas:
- Responde SIEMPRE en español
- Tono: cálido, directo, como una maestra apasionada
- **MÁXIMO 2-3 oraciones por respuesta. Sé muy breve y concisa.**
- Sé específica y práctica, nunca genérica
- Si te preguntan algo fuera del arte, redirige brevemente al tema
- Usa el contexto de la obra actual si se proporciona
- Empieza con algo positivo antes de sugerencias
- Al analizar el lienzo: menciona exactamente lo que ves en 2-3 oraciones máximo"""

VISION_PROMPT = """Eres Pixi — profesor experto en arte analizando el lienzo de un estudiante en tiempo real.

PERSPECTIVA DE CÁMARA: La cámara está montada en ángulo superior/cenital, mirando hacia abajo sobre el lienzo. SIEMPRE interpreta las imágenes como una vista aérea desde arriba:
- El lienzo ocupa la mayor parte del encuadre visto desde arriba
- La mano/pincel del artista puede aparecer entrando desde los bordes del frame
- Los trazos se ven desde arriba — su ancho, dirección y textura son claramente visibles
- Las zonas más claras indican luz zenital directa; las más oscuras pueden ser sombras de la mano o relieves de pintura

CONTORNOS PROYECTADOS — CRÍTICO:
El sistema proyecta los contornos de la obra maestra directamente sobre el lienzo como guías de dibujo. DEBES distinguir:
- PROYECCIÓN (ignora para evaluar): líneas finas, planas, luminosas, sin textura — son las guías del proyector
- PINTURA REAL (evalúa esto): tiene textura visible, brillo húmedo, grosor, bordes orgánicos, opacidad
- El estudiante pinta dentro y sobre los contornos proyectados para reproducir la obra
- NUNCA confundas los contornos proyectados con avance de pintura — solo evalúa la pintura real

Tienes una secuencia de fotogramas tomados cada 0.5 segundos — úsalos para analizar el MOVIMIENTO y PROGRESO:

1. **Progreso observado** (empieza siempre positivo — ¿qué zona se pintó, qué mejoró?)
2. **Técnica desde arriba**: dirección de los trazos, presión (grosor visible), cobertura de pintura, uniformidad de capa
3. **Color y mezcla**: tonos exactos que ves en el lienzo, zonas bien logradas, áreas que necesitan más pigmento
4. **Una sugerencia inmediata y concreta** — específica para lo que ves en este momento desde la vista cenital

Menciona zonas concretas, colores exactos, trazos visibles desde arriba.
**MÁXIMO 3 oraciones. Muy breve. En español. Tono motivador y directo.**"""


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[list[Message]] = []
    artwork_title: Optional[str] = None
    artwork_artist: Optional[str] = None
    stage_title: Optional[str] = None
    stage_number: Optional[int] = None


class AnalyzeRequest(BaseModel):
    artwork_title: Optional[str] = None
    stage_title: Optional[str] = None
    stage_number: Optional[int] = None


class MonitorSessionRequest(BaseModel):
    artwork_title: str
    artwork_artist: Optional[str] = None
    stage_title: str
    stage_number: int


class MonitorStageRequest(BaseModel):
    stage_title: str
    stage_number: int


class ChatResponse(BaseModel):
    reply: str


async def capture_frames(n: int = 8, interval: float = 0.5) -> list[bytes]:
    """Captura n frames del live feed con intervalo entre ellos para analizar movimiento."""
    frames = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for _ in range(n):
                try:
                    res = await client.get(f"{VISION_NODE_URL}/capture")
                    if res.status_code == 200 and res.content:
                        frames.append(res.content)
                except Exception:
                    pass
                import asyncio
                await asyncio.sleep(interval)
    except Exception as e:
        log.warning("Vision capture failed: %s", e)
    return frames


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest):
    try:
        client = get_client()

        history = []
        for msg in (body.history or []):
            role = "user" if msg.role == "user" else "model"
            history.append(genai_types.Content(role=role, parts=[genai_types.Part(text=msg.content)]))

        context = ""
        if body.artwork_title:
            context = f"[Contexto: El estudiante está pintando '{body.artwork_title}'"
            if body.artwork_artist:
                context += f" de {body.artwork_artist}"
            if body.stage_title and body.stage_number:
                context += f", actualmente en la Etapa {body.stage_number}: {body.stage_title}"
            context += "]\n\n"

        full_message = context + body.message

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=history + [genai_types.Content(role="user", parts=[genai_types.Part(text=full_message)])],
            config=genai_types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )

        return ChatResponse(reply=response.text)

    except Exception as e:
        log.error("Gemini chat error: %s", e)
        return ChatResponse(reply="Lo siento, tuve un problema al procesar tu pregunta. Intenta de nuevo.")


@router.post("/monitor/start")
async def monitor_start(body: MonitorSessionRequest):
    from app.core.monitor import start_session
    start_session(body.artwork_title, body.artwork_artist or "", body.stage_title, body.stage_number)
    return {"status": "monitor started"}


@router.post("/monitor/stop")
async def monitor_stop():
    from app.core.monitor import stop_session
    stop_session()
    return {"status": "monitor stopped"}


@router.post("/monitor/stage")
async def monitor_update_stage(body: MonitorStageRequest):
    from app.core.monitor import update_stage
    update_stage(body.stage_title, body.stage_number)
    return {"status": "stage updated"}


@router.post("/analyze", response_model=ChatResponse)
async def analyze_canvas(body: AnalyzeRequest):
    """Captura secuencia de frames del live feed y pide a Gemini análisis de técnica."""
    try:
        frames = await capture_frames(n=8, interval=0.5)
        if not frames:
            return ChatResponse(reply="No pude acceder a la camara en este momento. Asegurate de que el nodo de vision este encendido.")

        client = get_client()

        context = ""
        if body.artwork_title:
            context = f"El estudiante está pintando '{body.artwork_title}'"
            if body.stage_title and body.stage_number:
                context += f", Etapa {body.stage_number}: {body.stage_title}"
            context += ". "

        prompt = context + f"Analiza esta secuencia de {len(frames)} fotogramas del live feed (tomados cada 0.5s) y da feedback detallado sobre técnica, trazos y agarre del pincel."

        parts = [genai_types.Part(text=prompt)]
        for frame in frames:
            parts.append(genai_types.Part(inline_data=genai_types.Blob(mime_type="image/jpeg", data=frame)))

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[genai_types.Content(role="user", parts=parts)],
            config=genai_types.GenerateContentConfig(system_instruction=VISION_PROMPT),
        )

        return ChatResponse(reply=response.text)

    except Exception as e:
        log.error("Vision analysis error: %s", e)
        return ChatResponse(reply="Tuve un problema analizando el lienzo. Intenta de nuevo.")
