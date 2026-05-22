# RPi4-B — PROYECTOR (192.168.0.192)

Proyecta las imágenes guía sobre el lienzo del estudiante.

## Servicio
```bash
systemctl status pixartek-projection
```

## Archivos
| Archivo | Descripción |
|---------|-------------|
| `main.py` | Servidor FastAPI — recibe comandos de proyección |
| `display.py` | Control del proyector |
| `config.py` | Resolución y configuración de pantalla |

## Endpoints (puerto 8001)
| Ruta | Descripción |
|------|-------------|
| POST /project | Proyectar imagen de etapa |
| POST /clear | Apagar proyección |
| POST /adjust | Ajustar posición/zoom |
| GET /status | Estado del proyector |
