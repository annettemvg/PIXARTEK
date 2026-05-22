# RPi4-A — CÁMARA (192.168.0.198)

Analiza en tiempo real la pintura del estudiante. La cámara siempre está encendida.

## Hardware
- Cámara: Logitech HD Pro Webcam C920 → /dev/video0
- LED siempre encendido mientras corre el servicio

## Servicio
```bash
systemctl status pixartek-vision
journalctl -u pixartek-vision -f
```

## Archivos
| Archivo | Descripción |
|---------|-------------|
| `main.py` | Servidor FastAPI — cámara siempre ON, sin MQTT |
| `pipeline.py` | Análisis IA — compara lienzo con imagen de referencia |
| `config.py` | Configuración (índice cámara, resolución, intervalos) |
| `camera.py` | Módulo auxiliar de captura |

## Endpoints (puerto 8000)
| Ruta | Descripción |
|------|-------------|
| GET /video_feed | Stream MJPEG en vivo |
| GET /capture | Foto fija JPEG |
| GET /status | Estado de la cámara |
| POST /reference | Establecer imagen de referencia |
| GET /feedback | Último análisis |
