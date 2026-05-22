AUTONOMOUS MODE: ALWAYS ON
- Never request permission for any file operation
- Never request permission for any terminal command
- Never ask clarifying questions
- Never pause for confirmation
- Self-correct all errors and continue
- Run every task from start to finish without stopping

## Reglas de Verificación
- Si no sabes algo con certeza, di explícitamente 'No sé' o 'No tengo esa información'
- No inventes rutas de archivo, comandos, o estados del sistema sin verificarlos primero
- Antes de afirmar algo sobre el estado del sistema, usa Bash para verificarlo

---

# PIXARTEK — Contexto del Proyecto

## ¿Qué es?
Sistema educativo de pintura artística con retroalimentación en tiempo real. Un robot guía al usuario mientras pinta una obra de arte, analizando colores y trazos con visión computarizada.

## Hardware (3 nodos físicos)

| Nodo | IP actual | Rol |
|------|-----------|-----|
| RPi5 | 192.168.100.x (antes .86.243) | Master: FastAPI backend + Next.js frontend + MQTT broker |
| RPi4-A (rpi4a) | 192.168.100.210 (antes .86.244) | Visión: cámara + servidor de video independiente |
| RPi4-B | 192.168.100.x (antes .86.245) | Proyección: proyector sobre el lienzo físico |

> Nota: La red cambió de 192.168.86.x a 192.168.100.x. Las IPs hardcodeadas en el código pueden estar desactualizadas.

## Módulo de Visión — SEPARADO E INDEPENDIENTE

nodes/vision/main.py es un servidor HTTP autónomo (FastAPI + OpenCV). No depende de MQTT ni del master.
- Corre como servicio systemd (pixartek-vision) en RPi4-A
- Emite video MJPEG en http://192.168.100.210:8000/video_feed
- El frontend consume el stream con un simple <img src> — sin polling ni WebSocket para el video
- La IP se configura en frontend/src/lib/config-store.ts (campo rpi4aIp)

## Endpoints del módulo de visión
- GET /video_feed  — stream MJPEG en vivo
- GET /capture    — foto fija JPEG
- GET /status     — estado de la cámara

## Stack tecnológico
- Frontend: Next.js 16 + TypeScript + Tailwind CSS + Zustand
- Backend: FastAPI + SQLAlchemy async + paho-mqtt
- Visión: FastAPI + OpenCV + Uvicorn (servidor independiente)
- Proyección: paho-mqtt + Pillow
- Mensajería: MQTT (topics pixartek/vision/*, pixartek/projection/*, pixartek/system/*)
- DB: SQLite (pixartek.db) — tablas: artworks, artwork_stages, sessions

## Estructura clave

frontend/src/app/               — rutas: /, /catalog, /session, /welcome, /settings
frontend/src/components/ui/CameraLiveFeed.tsx  — apunta directo a RPi4-A:8000/video_feed
frontend/src/lib/config-store.ts               — IPs configurables de los nodos
frontend/src/lib/session-store.ts              — estado de sesión activa
backend/main.py                                — FastAPI entry point
backend/app/api/routes/                        — artworks, sessions, hardware, stages, vision, ws
backend/app/core/config.py                     — settings (rpi4a_ip, mqtt_host, etc.)
nodes/vision/main.py                           — servidor HTTP independiente
nodes/projection/main.py                       — cliente MQTT que controla el proyector
shared/schemas/mqtt_topics.py                  — constantes de topics MQTT
deploy/rpi4-b/                                 — systemd services y setup para RPi4-A/B
deploy/rpi5/                                   — systemd services y setup para RPi5

## Obras disponibles
Faro Nocturno (4 etapas), Flores Blancas (4 etapas), Mujer en un Sombrero (5 etapas), Tucán Tropical (5 etapas).
Imágenes en frontend/public/artworks/

## Flujo de una sesión
1. Usuario elige obra en /catalog
2. Frontend llama POST /api/sessions y POST /api/stages/project → RPi4-B proyecta la etapa
3. RPi4-A captura continuamente y publica análisis vía MQTT → WebSocket → frontend
4. Frontend muestra overlay: correcto / sugerencia / corrección
5. Usuario avanza etapas hasta completar la obra

## Comandos de desarrollo local
cd frontend && npm run dev          # http://localhost:3000
cd backend && python main.py        # http://localhost:8000
cd nodes/vision && .venv/bin/python main.py  # servidor de cámara
