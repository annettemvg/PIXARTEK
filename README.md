# 🎨 PIXARTEK - Robot Educativo de Pintura Artística

> Un sistema inteligente de asistencia para pintura artística usando Raspberry Pi, visión computarizada y análisis en tiempo real.

![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 🚀 Descripción General

PIXARTEK es una plataforma educativa que proporciona retroalimentación en tiempo real mientras creas arte. Utilizando un sistema distribuido de Raspberry Pi y análisis de visión computarizada, ofrece:

- **Análisis de Color en Vivo** - Detección de colores y pigmentación
- **Feedback Instantáneo** - Sugerencias sobre qué colores faltan
- **Registro de Sesiones** - Seguimiento de obras y sesiones de pintura
- **Interfaz Intuitiva** - Panel de control web en tiempo real

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│           PIXARTEK DISTRIBUTED SYSTEM               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  RPI5 (192.168.86.243)        RPI4A (192.168.86.244)│
│  Master Control               Vision Node            │
│  ├─ Next.js (3000)            ├─ Camera Capture    │
│  ├─ FastAPI (8000)            ├─ OpenCV Analysis   │
│  ├─ HTTP Server (9999)        └─ MQTT Publisher    │
│  └─ MQTT Broker (1883)                              │
│                                                     │
│  RPI4B (192.168.86.245)                            │
│  Projection Node                                    │
│  └─ Projector Control                              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 📋 Estructura del Proyecto

```
pixartek/
├── frontend/                  # Next.js React Application
│   ├── src/
│   │   ├── app/             # App routes and layout
│   │   ├── components/      # React components
│   │   │   ├── ui/         # UI components (CameraLiveFeed, etc)
│   │   │   ├── modals/     # Modal components
│   │   │   └── sections/   # Page sections
│   │   ├── lib/            # Utilities and helpers
│   │   └── styles/         # Tailwind CSS
│   ├── public/             # Static assets
│   ├── package.json
│   └── next.config.js
│
├── backend/                   # FastAPI Backend
│   ├── main.py             # Main application
│   ├── models/             # Data models
│   ├── routes/             # API endpoints
│   └── requirements.txt
│
├── nodes/                     # RPi-specific services
│   ├── vision/             # RPI4A Vision processing
│   │   ├── main.py        # Vision service main
│   │   ├── camera.py      # Camera interface
│   │   ├── calibration.py # Color calibration
│   │   └── pipeline.py    # Analysis pipeline
│   │
│   └── projection/         # RPI4B Projection control
│       └── main.py
│
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   └── API.md
│
├── .gitignore
├── README.md
└── LICENSE
```

## ⚡ Quick Start

### Requisitos Previos

- **Hardware:**
  - Raspberry Pi 5 (Master/Frontend)
  - Raspberry Pi 4A (Vision Node)
  - Raspberry Pi 4B (Projection Node - Opcional)
  - Cámara compatible con OpenCV
  - Red conectada

- **Software:**
  - Node.js 18+ (para frontend)
  - Python 3.9+ (para backend/vision)
  - Git

### Instalación Local

#### 1. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
# Accede a http://localhost:3000
```

#### 2. Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
# API disponible en http://localhost:8000
```

#### 3. Nodo de Visión (RPI4A)

```bash
cd nodes/vision
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## 🌐 Deployment

### Vercel (Frontend)

El frontend está optimizado para Vercel. Desplegar es tan simple como:

1. Conectar repositorio GitHub a Vercel
2. Seleccionar carpeta `frontend`
3. Vercel detectará Next.js automáticamente
4. Deploy con un clic

**Live Demo:** [pixartek.vercel.app](https://pixartek.vercel.app)

### Backend & Vision Nodes

- **Backend:** Dockerizado para desplegar en cualquier servidor
- **Vision Nodes:** Se ejecutan localmente en Raspberry Pi con systemd

## 🔌 API Endpoints

### Vision Analysis

```
POST /api/analysis
Body: {
  "artwork_id": "string",
  "canvas_state": "jpeg_base64",
  "current_colors": ["#FF0000", "#00FF00"]
}
Response: {
  "missing_colors": ["#0000FF"],
  "pigment_suggestions": ["Azul Cobalto"],
  "composition_feedback": "string"
}
```

### Artwork Management

```
GET /api/artworks              # Listar obras
POST /api/artworks             # Crear obra
GET /api/artworks/{id}         # Obtener obra
PUT /api/artworks/{id}         # Actualizar obra
POST /api/artworks/{id}/analyze # Analizar obra
```

## 🎥 Live Feed System

El sistema de live feed captura frames en tiempo real:

- **Captura:** RPI4A captura 30 FPS
- **Sincronización:** Frames se sincronizan cada 200ms a RPI5
- **Transmisión:** HTTP server sirve frames JPEG
- **Display:** React component muestra video en vivo

```
RPI4A Camera → /tmp/latest_canvas.jpg 
  ↓ [SSH/SCP sync every 200ms]
RPI5 HTTP Server → /tmp/camera_frame.jpg
  ↓ [HTTP GET]
React Component → Browser Display
```

## 🛠️ Tecnologías Utilizadas

### Frontend
- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **WebSocket** - Real-time updates

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **MQTT** - Message broker

### Vision
- **OpenCV (cv2)** - Computer vision
- **NumPy** - Numerical computing
- **Scikit-image** - Image processing

### Infrastructure
- **Raspberry Pi** - Edge computing
- **systemd** - Service management
- **Docker** - Containerization (opcional)
- **Vercel** - Frontend hosting

## 📊 Monitoreo y Logs

### Frontend
```bash
# Ver logs de Next.js
tail -f /tmp/nextjs.log

# Ver status
curl http://localhost:3000
```

### Vision Service
```bash
# Ver status del servicio
sudo systemctl status pixartek-vision

# Ver logs
journalctl -u pixartek-vision -n 100 --no-pager
```

### Frame Sync
```bash
# Verificar sincronización
ls -lh /tmp/camera_frame.jpg
stat /tmp/camera_frame.jpg
```

## 🐛 Troubleshooting

### Live Feed aparece en negro
1. Verificar vision service: `systemctl status pixartek-vision`
2. Verificar frame en RPI4A: `ls /tmp/latest_canvas.jpg`
3. Verificar sync script: `pgrep -f sync_camera_frames`
4. Verificar HTTP server: `curl http://localhost:9999/camera_frame.jpg`

### API no responde
1. Verificar backend: `curl http://localhost:8000/docs`
2. Revisar logs: `tail -f /tmp/backend.log`
3. Reiniciar servicio: `sudo systemctl restart pixartek-backend`

### Conexión RPI's lenta
1. Verificar red: `ping 192.168.86.244`
2. Verificar SSH: `ssh pi@192.168.86.244 "echo OK"`
3. Reiniciar red: `sudo systemctl restart networking`

## 📈 Performance

- **Latencia de Frame:** ~200ms
- **Throughput:** ~50 Mbps (red local)
- **Memoria Frontend:** ~80MB
- **CPU Vision:** ~45% (RPI4A)

## 📝 Changelog

### v1.0.0 (2026-05-02)
- ✅ Live camera feed system operativo
- ✅ Análisis de visión en tiempo real
- ✅ Interfaz web responsive
- ✅ Sistema distribuido stable

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Para soporte, contacta o abre un issue en GitHub.

## 📄 Licencia

Este proyecto está bajo licencia MIT - ver archivo `LICENSE` para detalles.

## 👨‍💻 Autor

**PIXARTEK Team**
- **Created:** 2026
- **Status:** Active Development

---

**¿Preguntas?** Abre un issue o contacta directamente.

**Última actualización:** 2026-05-02
