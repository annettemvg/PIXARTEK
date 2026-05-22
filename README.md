# PIXARTEK — Sistema de Arte Interactivo

Sistema distribuido de 4 Raspberry Pi que guía a estudiantes en la creación de obras de arte mediante análisis de visión artificial, dispensación automática de pigmentos y proyección de imágenes guía.

---

## 🗺️ Arquitectura General

```
┌──────────────────────────────────────────────────────────────┐
│                      RED LOCAL (192.168.0.x)                  │
│                                                                │
│   RPi5 (197)           RPi4-A (198)        RPi4-B (192)      │
│  ┌───────────┐         ┌──────────┐        ┌──────────┐      │
│  │    APP    │◄───────►│  CÁMARA  │        │PROYECTOR │      │
│  │  Backend  │  HTTP   │ Análisis │        │ Imágenes │      │
│  │ Frontend  │         │  Video   │        │  guía    │      │
│  │ Actuador  │         └──────────┘        └──────────┘      │
│  │Dispensador│                                                 │
│  └───────────┘         Cleaning (149)                        │
│                        ┌──────────┐                           │
│                        │ LIMPIEZA │                           │
│                        │ Pinceles │                           │
│                        └──────────┘                           │
└──────────────────────────────────────────────────────────────┘
```

---

## 📦 Estructura del Repositorio

```
pixartek/
├── README.md
├── backend/                  → API Python FastAPI  ──────────► corre en RPi5
├── frontend/                 → App Next.js (kiosk) ──────────► corre en RPi5
├── nodes/
│   ├── actuator/             → Motor dispensador   ──────────► corre en RPi5
│   ├── vision/               → Cámara + análisis IA ─────────► corre en RPi4-A
│   └── projection/           → Control proyector   ──────────► corre en RPi4-B
└── deploy/
    ├── rpi5/                 → Instalación RPi5
    ├── rpi4-a/               → Instalación RPi4-A (cámara)
    └── rpi4-b/               → Instalación RPi4-B (proyector)
```

---

## 🍓 RPi5 — APP + ACTUADOR `192.168.0.197`

**Cerebro del sistema.** Corre el backend, el frontend kiosk y controla el motor stepper que dispensa los pigmentos.

### Servicios
```bash
systemctl status pixartek-backend     # API Python  → puerto 8000
systemctl status pixartek-frontend    # Next.js     → puerto 3000
systemctl status mosquitto            # MQTT broker → puerto 1883
```

### Backend (`backend/`)
API FastAPI con todos los endpoints del sistema.

```
backend/
├── main.py                        → Punto de entrada
├── app/
│   ├── api/routes/
│   │   ├── artworks.py            → Catálogo de obras
│   │   ├── sessions.py            → Sesiones de pintura
│   │   ├── hardware.py            → Control actuador y dispensación
│   │   ├── vision.py              → Proxy hacia cámara RPi4-A
│   │   ├── projection.py          → Proxy hacia proyector RPi4-B
│   │   ├── chat.py                → IA Pixi (Gemini)
│   │   ├── tts.py                 → Texto a voz
│   │   └── ws.py                  → WebSocket tiempo real
│   ├── core/
│   │   ├── monitor.py             → Monitor de sesión con Gemini
│   │   └── config.py              → Variables de entorno
│   └── db/
│       ├── base.py                → Modelos SQLite
│       └── seed.py                → Datos iniciales
```

### Frontend (`frontend/`)
Kiosk táctil Next.js. El estudiante lo ve en la pantalla principal.

```
frontend/src/app/
├── page.tsx              → Pantalla de inicio
├── catalog/              → Catálogo de obras
├── session/              → Sesión activa de pintura (pantalla principal)
├── settings/             → Configuración del kiosk
└── signin/               → Identificación del estudiante
```

### Actuador — Dispensador de Pigmentos (`nodes/actuator/`)

Motor stepper TMC2209 que recorre un riel y dispensa pigmentos en cada cubículo.

```
nodes/actuator/
├── actuador.py                → Ciclo completo: MIN → dispensa → MAX → MIN
├── actuador_home.py           → Ir a posición mínima (HOME)
├── actuador_max.py            → Ir a posición máxima
├── actuador_medir.py          → Medir pasos totales del recorrido
├── actuador_posiciones.py     → Guardar posiciones de parada
├── actuador_dispense.py       → Dispensar en posición específica
├── actuador_btn.py            → Control manual con botón físico
└── colors/
    ├── flores-blancas/
    │   ├── ciclo_flores_blancas.py    → Ciclo completo (4 colores)
    │   ├── burnt_sienna.py
    │   ├── champagne.py
    │   ├── ivory_white.py
    │   └── lime_green.py
    ├── faro-nocturno/
    │   ├── ciclo_faro_nocturno.py     → Ciclo completo (4 colores)
    │   ├── amarillo_dorado.py
    │   ├── naranja.py
    │   ├── indigo.py
    │   └── black.py
    ├── mujer-azul/
    │   ├── ciclo_mujer_sombrero.py    → Ciclo completo (5 colores)
    │   ├── baby_blue.py
    │   ├── azul_cobalto.py
    │   ├── purple.py
    │   ├── lime_green.py
    │   └── black.py
    └── tucan-tropical/
        ├── ciclo_tucan_tropical.py    → Ciclo completo (4 colores)
        └── tucan tropical/
            ├── dark_navy.py
            ├── amber.py
            ├── green.py
            └── teal.py
```

#### Pines GPIO (RPi5 / gpiochip4)
| Pin | Función |
|-----|---------|
| GPIO 2 | STEP — pulsos de movimiento |
| GPIO 3 | DIR — dirección (0=izquierda, 1=derecha) |
| GPIO 4 | EN — habilitar motor (0=activo, 1=apagado) |
| GPIO 5 | LIMIT_MIN — sensor fin de carrera izquierdo |
| GPIO 6 | LIMIT_MAX — sensor fin de carrera derecho |

#### Posiciones de parada (pasos desde LIMIT_MIN)
| Posición | Pasos | Descripción |
|----------|-------|-------------|
| HOME | 0 | Primera dispensación (sin mover) |
| Parada 1 | 60,338 | Segundo cubículo |
| Parada 2 | 129,148 | Tercer cubículo |
| Parada 3 | 200,036 | Cuarto cubículo |
| Parada 4 | 263,943 | Quinto cubículo |
| LIMIT_MAX | ~316,000 | Fin de recorrido |

---

## 📷 RPi4-A — CÁMARA `192.168.0.198`

**Analiza en tiempo real la pintura del estudiante.** Compara el lienzo con la imagen de referencia y envía feedback de precisión al sistema.

La cámara **siempre está encendida** desde que arranca el servicio.

### Servicio
```bash
systemctl status pixartek-vision
journalctl -u pixartek-vision -f    # ver logs en tiempo real
```

### Código (`nodes/vision/`)
```
nodes/vision/
├── main.py        → Servidor FastAPI — cámara siempre ON al iniciar
├── pipeline.py    → Análisis de imagen IA (comparación con referencia)
├── config.py      → Configuración (índice cámara, resolución, intervalos)
└── camera.py      → Módulo auxiliar de captura
```

### Hardware
- **Cámara:** Logitech HD Pro Webcam C920
- **Dispositivo:** `/dev/video0`
- **LED:** Siempre encendido mientras el servicio corre

### Endpoints HTTP (puerto 8000)
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `GET /video_feed` | GET | Stream MJPEG en vivo |
| `GET /capture` | GET | Foto fija JPEG |
| `GET /status` | GET | Estado de la cámara y análisis |
| `POST /reference` | POST | Establecer imagen de referencia |
| `GET /feedback` | GET | Último resultado de análisis |
| `POST /camera/on` | POST | Compatibilidad (cámara ya siempre activa) |
| `POST /camera/off` | POST | Ignorado — cámara permanece activa siempre |

---

## 📽️ RPi4-B — PROYECTOR `192.168.0.192`

**Proyecta las imágenes guía sobre el lienzo del estudiante.** Muestra los contornos y divisiones de cada etapa de la obra directamente sobre el papel/lienzo.

### Servicio
```bash
systemctl status pixartek-projection
```

### Código (`nodes/projection/`)
```
nodes/projection/
├── main.py      → Servidor FastAPI — recibe comandos de proyección
├── display.py   → Control del display y proyector
└── config.py    → Resolución y configuración de pantalla
```

### Endpoints HTTP (puerto 8001)
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `POST /project` | POST | Proyectar imagen de etapa |
| `POST /clear` | POST | Apagar proyección (pantalla negra) |
| `POST /adjust` | POST | Ajustar posición/zoom |
| `GET /status` | GET | Estado del proyector |

### Imágenes
Las imágenes guía (contornos para proyectar) están en RPi5:
```
frontend/public/artworks/<OBRA>-DIVISIONES/Etapa<N>.png
```
RPi5 le dice a RPi4-B qué imagen proyectar vía HTTP.

---

## 🧼 Cleaning — LIMPIEZA `192.168.0.149`

**Estación automática de limpieza de pinceles.** Se activa cuando el estudiante presiona el botón "Limpiar Pincel" en el kiosk.

El backend en RPi5 envía el comando HTTP a esta estación.

---

## 🔌 Flujo de comunicación

```
Estudiante toca kiosk (RPi5:3000)
         │
         ▼
Backend API (RPi5:8000)
         ├──► RPi4-A:8000   → /reference (qué analizar)
         │                  → /feedback  (leer análisis)
         ├──► RPi4-B:8001   → /project   (qué proyectar)
         │                  → /clear     (apagar proyección)
         └──► Cleaning:80   → /clean     (limpiar pincel)

WebSocket (RPi5:8000/ws)
         └──► Frontend recibe feedback de análisis en tiempo real
```

---

## 🎨 Obras disponibles

| ID | Título | Colores |
|----|--------|---------|
| `flores-blancas` | Flores Blancas | Burnt Sienna → Champagne → Ivory White → Lime Green |
| `faro-nocturno` | Faro Nocturno | Amarillo Dorado → Naranja → Índigo → Negro |
| `mujer-sombrero` | Mujer en un Sombrero | Baby Blue → Azul Cobalto → Púrpura → Lima → Negro |
| `tucan-tropical` | Tucán Tropical | Dark Navy → Ámbar → Verde → Teal |

---

## ⚙️ Variables de entorno

**`backend/.env`**
```env
DATABASE_URL=sqlite:///./pixartek.db
GEMINI_API_KEY=your_key_here
MQTT_HOST=localhost
MQTT_PORT=1883
VISION_NODE_URL=http://192.168.0.198:8000
PROJECTION_NODE_URL=http://192.168.0.192:8001
CLEANING_NODE_URL=http://192.168.0.149:80
```

---

## 🚀 Instalación rápida

### RPi5
```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # editar con tus valores
systemctl enable --now pixartek-backend

# Frontend
cd frontend
npm install
npm run build
systemctl enable --now pixartek-frontend
```

### RPi4-A (Cámara)
```bash
cd nodes/vision
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
systemctl enable --now pixartek-vision
```

### RPi4-B (Proyector)
```bash
cd nodes/projection
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
systemctl enable --now pixartek-projection
```
