# PIXARTEK Vision System — Deployment & Configuration Guide

## System Architecture

```
┌─────────────────────────┐
│  RPI5 (Main System)     │
│  192.168.86.243         │
│ ┌─────────────────────┐ │
│ │ Backend (FastAPI)   │ │  → publishes to pixartek/projection/command
│ │ Frontend (Next.js)  │ │  → receives pixartek/vision/feedback via WebSocket
│ │ MQTT Broker         │ │  → listens on all pixartek/# topics
│ │ (Mosquitto)         │ │
│ └─────────────────────┘ │
└─────────────────────────┘
         ▲    │
         │    │ MQTT
         │    ▼
┌─────────────────────────┐
│  RPI4-B (Vision Node)   │
│  192.168.86.244         │
│ ┌─────────────────────┐ │
│ │ Vision Analyzer     │ │  ← subscribes to pixartek/projection/command
│ │ (nodes/vision/)     │ │  → publishes to pixartek/vision/feedback
│ │ - Camera capture    │ │  → publishes to pixartek/vision/metrics
│ │ - Frame analysis    │ │
│ │ - Reference loading │ │
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │ Projection Display  │ │  ← subscribes to pixartek/projection/command
│ │ (nodes/projection/) │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

## Configuration Status

### ✅ RPI5 (Main System) — CONFIGURED
- **Backend**: FastAPI with MQTT client support
- **MQTT Broker**: Mosquitto listening on port 1883
- **Frontend**: Next.js with WebSocket support for real-time feedback
- **WebSocket**: Endpoint `/ws` broadcasts all MQTT messages to connected clients
- **Session Management**: Publishes stage changes to `pixartek/projection/command`

### ⏳ RPI4-B (Vision Node) — PENDING DEPLOYMENT
- **Vision Code**: ✅ Ready in `/nodes/vision/`
- **Requirements**: 
  - Python 3 with OpenCV (`python3-opencv`)
  - Paho MQTT client (`python3-paho-mqtt`)
  - Picamera2 and libcamera (`python3-picamera2`, `libcamera-dev`)
  - USB camera with proper drivers
- **Systemd Service**: ✅ Ready in `/deploy/rpi4-b/pixartek-vision.service`

## Vision System Message Flow

```
1. USER STARTS PAINTING SESSION
   └─> Backend creates session & publishes to pixartek/projection/command
       {
         "session_id": "...",
         "artwork_id": "...",
         "stage": 1,
         "image_path": "/home/pi/pixartek/assets/artwork/artwork_001.jpg",
         "timestamp": ...
       }

2. VISION NODE RECEIVES PROJECTION COMMAND
   └─> Loads reference image from image_path
   └─> Sets current_artwork and current_stage

3. CAMERA CAPTURES FRAMES (EVERY ~2 SECONDS)
   └─> Frame is compared against reference image
   └─> Vision pipeline calculates:
       - precision_pct (0-100, % of pixels matching reference)
       - color_deviation (0-45, approximate delta-E color distance)
       - stroke_errors[] (zones where painting deviates significantly)
       - suggestions[] (actionable tips for improvement)

4. VISION NODE PUBLISHES FEEDBACK
   └─> Publishes to pixartek/vision/feedback:
       {
         "node": "rpi4-vision",
         "artwork_id": "...",
         "stage": 1,
         "precision_pct": 85.5,
         "color_deviation": 12.3,
         "stroke_errors": [
           {"zone": "superior-izquierda", "message": "Falta rojo..."}
         ],
         "suggestions": ["Buen progreso..."],
         "timestamp": ...
       }

5. BACKEND RECEIVES MQTT MESSAGE
   └─> Broadcasts to all WebSocket clients via ws.py

6. FRONTEND RECEIVES FEEDBACK
   └─> Session page receives message via useWebSocket hook
   └─> Determines feedback type:
       - If stroke_errors.length > 0 → show "corrección" overlay
       - Else if suggestions.length > 0 → show "sugerencia" overlay
       - Else if precision_pct > 85 → show "correcto" overlay
   └─> Displays FeedbackOverlay component
   └─> Auto-closes after 4 seconds

7. FEEDBACK OVERLAY DISPLAYS
   └─> Shows full-screen image (/feedback/{type}.png)
   └─> Plays sound (/feedback/{type}.wav)
   └─> Optional custom message at bottom
   └─> Close button in top-right corner
```

## Vision Analysis Pipeline

### Image Processing Steps
1. **Color Correction**: Apply calibrated color balance
2. **Perspective Warping**: Correct camera angle via homography matrix
3. **Canvas ROI Extraction**: Crop to painting canvas (configurable 10-80% margins)
4. **Resize & Compare**: Resize to 320x240 for fast processing
5. **Precision Calculation**: 
   - Compare pixel values using absolute difference
   - `precision_pct = 100 - (mean_pixel_diff / 255 * 100)`
6. **Color Deviation**:
   - Per-channel histogram analysis
   - Bhattacharyya distance scaled to delta-E-like range
7. **Stroke Error Detection**:
   - Divide canvas into 3×3 grid
   - Detect zones with > 35.0 mean pixel difference
   - Identify dominant color error (too much/too little R/G/B)

### Feedback Thresholds
- **Error Messages** (stroke_errors):
  - Triggered when zone_diff > 35.0
  - Messages: "Excess of {color} — reduce pigment" or "Missing {color} — add more pigment"

- **Suggestions** (suggestions):
  - **Precision**:
    - ≥ 90%: "Excelente trazo! Continúa con la misma técnica"
    - ≥ 75%: "Buen progreso — mejora la cobertura"
    - < 75%: "Cubre bien el lienzo antes de agregar detalles"
  - **Color**:
    - color_deviation > 10: "El color se aleja de la referencia"
    - color_deviation > 5: "Pequeña desviación de color"
  - **Complexity**:
    - > 2 error zones: "Varias zonas con errores — trabaja de arriba hacia abajo"

## Feedback Overlays

Three types of full-screen feedback, each with image + audio:

1. **CORRECTO** (Correct) — Positive feedback
   - Image: `/public/feedback/correcto.png` (mint green, 1920x1080)
   - Sound: `/public/feedback/correcto.wav` (two 150ms 800Hz beeps)
   - Trigger: No errors + no suggestions + precision > 85%

2. **SUGERENCIA** (Suggestion) — Improvement tips
   - Image: `/public/feedback/sugerencia.png` (sky blue, 1920x1080)
   - Sound: `/public/feedback/sugerencia.wav` (one 300ms 600Hz beep)
   - Trigger: Has suggestions but no stroke errors
   - Shows custom message with tip at bottom

3. **CORRECCIÓN** (Correction) — Error detected
   - Image: `/public/feedback/corrección.png` (coral red, 1920x1080)
   - Sound: `/public/feedback/corrección.wav` (three 100ms 400Hz beeps)
   - Trigger: Has stroke errors
   - Shows custom message with error zone and fix at bottom

## Environment Variables

### RPI5 Backend
```bash
# Backend config
MQTT_HOST=localhost          # MQTT broker address
MQTT_PORT=1883              # MQTT broker port
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
```

### RPI4-B Vision Node
```bash
# Vision node config
MQTT_HOST=192.168.86.243          # RPI5 IP address
MQTT_PORT=1883
NODE_ID=rpi4-vision
DEV_MODE=false                     # disable mock mode
CAMERA_INDEX=0                     # /dev/video0

# Camera settings
FRAME_WIDTH=1280
FRAME_HEIGHT=720
CAPTURE_FPS=5

# Canvas region of interest (normalized 0-1)
CANVAS_ROI_X=0.1
CANVAS_ROI_Y=0.1
CANVAS_ROI_W=0.8
CANVAS_ROI_H=0.8

# Reference images location
ASSETS_DIR=/home/pi/pixartek/frontend/public/artworks
```

## Deployment: RPI4-B Vision Node

### Prerequisites
- SSH access to RPI4-B as user `pi`
- RPI4 or equivalent with USB camera
- Camera drivers installed

### Step-by-Step Deployment

```bash
# 1. From your development machine, SSH to RPI4-B
ssh pi@192.168.86.244

# 2. Copy project files (use the deploy script for this)
cd /path/to/pixartek
./deploy/deploy.sh rpi4b

# Or manually:
cd /home/pi/pixartek/nodes/vision

# 3. Create Python virtual environment with system packages
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install --prefer-binary paho-mqtt numpy Pillow

# 5. Install OpenCV system package
sudo apt-get update
sudo apt-get install -y python3-opencv libcamera-dev python3-picamera2

# 6. Test camera
python3 -c "import camera; print('Camera OK')"

# 7. Configure environment
# Create .env file or export variables:
export MQTT_HOST=192.168.86.243
export NODE_ID=rpi4-vision
export DEV_MODE=false

# 8. Test vision node
python3 main.py

# 9. Install systemd service
sudo cp /home/pi/pixartek/deploy/rpi4-b/pixartek-vision.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pixartek-vision
sudo systemctl start pixartek-vision

# 10. Check status
sudo journalctl -u pixartek-vision -f
```

## Testing the Vision System

### Local Testing (Before RPI4-B Deployment)

1. **Mock Camera Mode**:
   - Set `DEV_MODE=true` in vision node
   - Uses synthetic frames instead of real camera
   - Useful for testing without hardware

2. **Test MQTT Connection**:
   ```bash
   mosquitto_sub -h 192.168.86.243 -t "pixartek/#"
   ```
   Then start a painting session and monitor messages

3. **Test Frontend Feedback Display**:
   - Start a session in the browser
   - You should see feedback overlays as the vision node sends feedback

### Integration Testing (After RPI4-B Deployment)

1. **Verify Vision Node Connected**:
   ```bash
   mosquitto_sub -h 192.168.86.243 -t "pixartek/system/heartbeat"
   # Should see heartbeat from vision node every 5 seconds
   ```

2. **Start Painting Session**:
   - Open PIXARTEK app on RPI5 kiosk
   - Select a painting and start a stage
   - Paint on the canvas

3. **Monitor Vision Feedback**:
   ```bash
   mosquitto_sub -h 192.168.86.243 -t "pixartek/vision/feedback"
   # Should see feedback messages every 2 seconds
   ```

4. **Verify Frontend Display**:
   - Check web browser console for any errors
   - Overlays should appear based on painting quality
   - Audio should play (if not muted)

## Troubleshooting

### Vision Node Not Connecting
```bash
# Check MQTT connection
sudo journalctl -u pixartek-vision | grep -i mqtt

# Test MQTT broker reachability
nc -zv 192.168.86.243 1883
```

### Camera Not Found
```bash
# List available cameras
ls /dev/video*

# Check permissions
groups pi  # should include 'video' group

# Test camera directly
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

### Reference Image Not Loading
```bash
# Check file exists and is readable
ls -l /home/pi/pixartek/frontend/public/artworks/

# Verify image format
file /home/pi/pixartek/frontend/public/artworks/artwork_001.jpg
```

### No Feedback Appearing in Frontend
```bash
# Check WebSocket connection
# Browser dev tools → Network → WS → look for /ws connection

# Check backend receiving MQTT messages
mosquitto_sub -h 192.168.86.243 -t "pixartek/vision/feedback"

# Check backend WebSocket broadcasting
# Backend logs should show "WS connected" and "MQTT rx pixartek/vision/feedback"
```

## Current Status (April 27, 2026)

✅ **Completed**:
- Vision analysis pipeline with OpenCV (nodes/vision/*)
- Backend MQTT client and WebSocket broadcast
- Frontend FeedbackOverlay component with auto-close
- Session management publishes reference images
- Feedback asset generation (overlays + sounds)
- Systemd service configuration for RPI4-B

⏳ **Pending**:
- Deploy vision node to RPI4-B (SSH authentication blocked)
- Configure vision node systemd service on RPI4-B
- Test end-to-end feedback flow with real camera
- Calibration on actual RPI4-B setup

🚫 **Blockers**:
- SSH access to RPI4-B (192.168.86.244) failing with "Permission denied (publickey,password)"
- Cannot deploy `/nodes/vision/` code to RPI4-B until SSH is resolved

## Next Steps

1. **Resolve SSH Access** to RPI4-B:
   - Option A: Reset password via Pi-hole dashboard or physical access
   - Option B: Add public SSH key to `~/.ssh/authorized_keys` on RPI4-B
   - Option C: Use alternative deployment method (USB drive, network boot)

2. **Deploy Vision Node**:
   - Use the `./deploy/deploy.sh rpi4b` script once SSH is available
   - OR manually follow Step-by-Step Deployment section above

3. **Test System End-to-End**:
   - Verify vision node is running: `systemctl status pixartek-vision`
   - Start a painting session and observe feedback overlays

4. **Calibration** (Optional but Recommended):
   - Run camera calibration sequence to improve accuracy
   - Publish MQTT message to `pixartek/vision/calibrate` to trigger

## File References

- **Vision Node**: `nodes/vision/` (main.py, pipeline.py, camera.py, calibration.py)
- **Backend**: `backend/app/api/routes/sessions.py` (publishes commands)
- **Frontend**: `frontend/src/app/session/page.tsx` (receives feedback)
- **Services**: `deploy/rpi4-b/*.service` (systemd units)
- **Deployment**: `deploy/deploy.sh`, `deploy/rpi4-b/setup.sh`
- **Config**: `nodes/vision/config.py`, `backend/app/core/config.py`
- **Assets**: `frontend/public/feedback/*.{png,wav}`
