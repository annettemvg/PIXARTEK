# RPi5 — APP + ACTUADOR (192.168.0.197)

Este es el cerebro del sistema. Corre el backend, el frontend kiosk y controla el motor dispensador de pigmentos.

## Servicios
```bash
systemctl status pixartek-backend     # API → puerto 8000
systemctl status pixartek-frontend    # Kiosk → puerto 3000
systemctl status mosquitto            # MQTT → puerto 1883
```

## Carpetas
| Carpeta | Descripción |
|---------|-------------|
| `backend/` | API FastAPI — sesiones, artworks, hardware, IA |
| `frontend/` | Pantalla táctil del estudiante (Next.js) |
| `actuator/` | Motor stepper que dispensa los pigmentos |
