# PIXARTEK Vision System — Integration Checklist

## Backend Integration ✅

### MQTT Client
- [x] `app/mqtt/client.py` — MQTT connection with callbacks
- [x] `start_mqtt()` — connects to broker at startup
- [x] `publish()` — sends MQTT messages
- [x] Broadcast mechanism — forwards MQTT messages to WebSocket clients

### Session Management
- [x] `app/api/routes/sessions.py` — session creation/advancement
- [x] `_publish_projection()` — sends stage image_path to `pixartek/projection/command`
- [x] Message format includes: session_id, artwork_id, stage, image_path, timestamp
- [x] Image path construction: `/home/pi/pixartek/assets/artwork/{artwork_id}.jpg`

### WebSocket Integration
- [x] `app/api/routes/ws.py` — WebSocket endpoint at `/ws`
- [x] Registers with MQTT client via `register_broadcast()`
- [x] Broadcasts all MQTT messages to connected browsers
- [x] Sends JSON format: `{topic, payload}`
- [x] Auto-reconnect on disconnect

### Startup
- [x] `app/main.py` — initializes MQTT at startup
- [x] Sets event loop for async broadcast

## Frontend Integration ✅

### WebSocket Connection
- [x] `hooks/useWebSocket.ts` — connects to `ws://{hostname}:8000/ws`
- [x] Parses incoming JSON messages
- [x] Calls onMessage callback
- [x] Auto-reconnect with 3-second delay
- [x] Connection status tracking (connecting/connected/disconnected)

### Feedback Display
- [x] `components/feedback/FeedbackOverlay.tsx` — fullscreen overlay component
- [x] Props: type (correcto|sugerencia|corrección), visible, onClose, message
- [x] Loads image from `/feedback/{type}.png`
- [x] Plays audio from `/feedback/{type}.wav`
- [x] Auto-closes after 4 seconds
- [x] Close button in top-right
- [x] Optional message display at bottom

### Session Page Integration
- [x] `app/session/page.tsx` — uses useWebSocket hook
- [x] Listens for `pixartek/vision/feedback` messages
- [x] State management for feedback overlay
- [x] Feedback type determination logic:
  - stroke_errors.length > 0 → "corrección" with error message
  - suggestions.length > 0 → "sugerencia" with suggestion
  - precision_pct > 85 → "correcto"
- [x] Renders FeedbackOverlay component
- [x] Closes overlay on user click or timeout

## Assets ✅

### Feedback Overlays
- [x] `public/feedback/correcto.png` — 1920x1080, mint background
- [x] `public/feedback/sugerencia.png` — 1920x1080, sky blue background
- [x] `public/feedback/corrección.png` — 1920x1080, coral background

### Audio Files
- [x] `public/feedback/correcto.wav` — two 150ms 800Hz beeps
- [x] `public/feedback/sugerencia.wav` — one 300ms 600Hz beep
- [x] `public/feedback/corrección.wav` — three 100ms 400Hz beeps

## Vision Node Implementation ✅

### Main Module
- [x] `nodes/vision/main.py` — entry point with MQTT loop
- [x] Subscribes to `pixartek/vision/calibrate` and `pixartek/projection/command`
- [x] Publishes to `pixartek/vision/feedback` and `pixartek/vision/metrics`
- [x] Heartbeat loop at 5-second interval
- [x] Analysis loop at 2-second interval
- [x] Graceful shutdown handling

### Analysis Pipeline
- [x] `nodes/vision/pipeline.py` — frame analysis pipeline
- [x] `set_reference()` — loads reference image
- [x] `analyze()` — compares frame against reference
- [x] Returns FeedbackResult with:
  - precision_pct (0-100)
  - color_deviation (approx delta-E)
  - stroke_errors[] (zones with problems)
  - suggestions[] (improvement tips)

### Camera Module
- [x] `nodes/vision/camera.py` — camera capture interface
- [x] Supports multiple backends: cv2.VideoCapture, picamera2
- [x] Mock mode for dev/testing

### Calibration Module
- [x] `nodes/vision/calibration.py` — color & perspective calibration
- [x] `apply_color()` — color correction
- [x] `apply_homography()` — perspective warp
- [x] `calibrate_perspective()` — learn canvas corners
- [x] `calibrate_color()` — learn color response

### Configuration
- [x] `nodes/vision/config.py` — environment-based configuration
- [x] MQTT_HOST, MQTT_PORT, NODE_ID
- [x] Camera settings: width, height, FPS
- [x] Canvas ROI: x, y, w, h (normalized 0-1)
- [x] ASSETS_DIR for reference images

## Systemd Services ✅

### RPI5 Backend
- [x] `deploy/rpi5/pixartek-backend.service` — FastAPI service
- [x] Type=simple, auto-restart on failure
- [x] Runs as user pi
- [x] Working directory: /home/pi/pixartek/backend

### RPI4-B Vision
- [x] `deploy/rpi4-b/pixartek-vision.service` — Vision node service
- [x] Type=simple, auto-restart on failure
- [x] Runs as user pi
- [x] Working directory: /home/pi/pixartek/nodes/vision

## Deployment Scripts ✅

### Master Deploy
- [x] `deploy/deploy.sh` — orchestrates deployment to all nodes
- [x] Supports: all | rpi5 | rpi4a | rpi4b | status
- [x] SSH configuration via `deploy/.env`
- [x] Uses rsync for code sync
- [x] Runs setup.sh on each node

### Setup Scripts
- [x] `deploy/rpi5/setup.sh` — backend + MQTT + frontend setup
- [x] `deploy/rpi4-b/setup.sh` — vision + projection setup
- [x] Package installation
- [x] Virtual environment creation
- [x] Systemd service installation

## MQTT Topics

| Topic | Direction | Publisher | Subscriber | Payload |
|-------|-----------|-----------|------------|---------|
| `pixartek/projection/command` | RPI5 → RPI4-B | Backend | Vision Node | {session_id, artwork_id, stage, image_path, timestamp} |
| `pixartek/vision/feedback` | RPI4-B → RPI5 | Vision Node | Backend | {node, artwork_id, stage, precision_pct, color_deviation, stroke_errors[], suggestions[], timestamp} |
| `pixartek/vision/metrics` | RPI4-B → RPI5 | Vision Node | Backend | {node, session_id, stage, precision_pct, timestamp} |
| `pixartek/vision/calibrate` | RPI5 → RPI4-B | Backend | Vision Node | {canvas_corners} |
| `pixartek/system/heartbeat` | RPI4-B → RPI5 | Vision Node | Backend | {node, status, timestamp} |

## Message Flow Verification

### Flow 1: Session Start
```
1. User clicks "¡Pintar ahora!" on catalog page
2. Frontend: router.push(`/session?artwork=...&stage=...`)
3. Backend: POST /sessions {artwork_id, start_stage, total_stages}
4. Backend: create session record, save to database
5. Backend: publish "pixartek/projection/command" {image_path, ...}
6. Vision Node: receive command, load reference image
7. Backend: respond with session JSON

Expected:
- Session created in database ✓
- MQTT message published ✓
- Vision node loads reference ✓
```

### Flow 2: Frame Analysis
```
1. Vision node runs analysis loop (every 2 seconds)
2. Camera: capture frame
3. Pipeline: compare against reference
4. Pipeline: calculate precision, color_deviation, errors, suggestions
5. Vision node: publish "pixartek/vision/feedback" {precision_pct, ...}
6. Backend: receive MQTT message
7. Backend: broadcast to WebSocket clients
8. Frontend: receive feedback message
9. Frontend: determine feedback type
10. Frontend: render FeedbackOverlay component
11. FeedbackOverlay: load image, play audio, auto-close after 4 seconds

Expected:
- Feedback published every 2 seconds ✓
- Frontend receives via WebSocket ✓
- Overlay displays correctly ✓
- Audio plays ✓
- Auto-closes ✓
```

### Flow 3: Stage Advancement
```
1. User clicks "Siguiente etapa" (Next stage)
2. Backend: PATCH /sessions/{id}/stage {stage: 2}
3. Backend: update current_stage in database
4. Backend: publish "pixartek/projection/command" {stage: 2, ...}
5. Vision Node: receive command, load reference for stage 2
6. Frontend: navigate to next stage in UI

Expected:
- Stage updated in database ✓
- New reference image loaded ✓
- Feedback continues for new stage ✓
```

## Testing Procedures

### Test 1: MQTT Connection
```bash
# Terminal 1: Monitor all MQTT messages
mosquitto_sub -h 192.168.86.243 -t "pixartek/#" -v

# Terminal 2: Start a session (should see projection/command)
curl -X POST http://192.168.86.243:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"artwork_id":"artwork_001","start_stage":1,"total_stages":5}'

# Expected output in Terminal 1:
# pixartek/projection/command {"session_id":"...","artwork_id":"...","stage":1,...}
```

### Test 2: WebSocket Connection
```bash
# Browser DevTools → Network → WS
# Should see ws://192.168.86.243:8000/ws → 101 Switching Protocols

# Open session page, WebSocket should connect
# Monitor in DevTools → check incoming frames
```

### Test 3: Feedback Overlay
```
1. Open PIXARTEK app on browser
2. Start a painting session
3. Wait 2-3 seconds for first feedback (vision node may be initializing)
4. You should see:
   - Feedback overlay image (correcto/sugerencia/corrección)
   - Audio plays (if not muted)
   - Overlay auto-closes after 4 seconds
5. Repeat 2-3 times to verify different feedback types
```

### Test 4: Canvas ROI Accuracy
```bash
# Test with different camera angles to verify perspective correction
# Verify calibration was run on the vision node:
mosquitto_sub -h 192.168.86.243 -t "pixartek/vision/calibrate"
```

## Troubleshooting by Symptom

### "No feedback appearing"
- [ ] Check vision node is running: `systemctl status pixartek-vision`
- [ ] Check MQTT messages: `mosquitto_sub -t pixartek/vision/feedback`
- [ ] Check camera is connected: `ls /dev/video*`
- [ ] Check reference image exists: `ls /home/pi/pixartek/assets/artwork/`
- [ ] Check frontend WebSocket connected: Browser DevTools

### "Feedback appearing but overlays don't display"
- [ ] Check feedback asset files exist: `ls /public/feedback/`
- [ ] Check browser console for errors (DevTools)
- [ ] Check FeedbackOverlay component receives props
- [ ] Verify CSS classes are loaded

### "Overlays display but audio doesn't play"
- [ ] Check audio files exist: `ls /public/feedback/*.wav`
- [ ] Check browser audio permissions
- [ ] Check volume is not muted
- [ ] Check audio context initialization in React

### "Vision node receiving commands but not analyzing"
- [ ] Check MQTT_HOST is correct (should be 192.168.86.243)
- [ ] Check camera initialization: vision node logs should show "Camera init OK"
- [ ] Check reference image path is valid (must be readable by pi user)
- [ ] Check camera permissions: `groups pi` (should include 'video')

## Deployment Status

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| Backend | RPI5 (192.168.86.243) | Ready | MQTT client + WebSocket |
| Frontend | RPI5 (192.168.86.243) | Ready | FeedbackOverlay component |
| Vision Node | RPI4-B (192.168.86.244) | Ready (code) | Requires SSH deployment |
| MQTT Broker | RPI5 (192.168.86.243) | Ready | Mosquitto on port 1883 |
| Services | All | Ready (files) | Systemd units ready, await deployment |
| Feedback Assets | Frontend public/ | Ready | PNG + WAV files generated |

## Blockers & Next Steps

### Current Blocker: SSH Access to RPI4-B
```
Issue: Cannot SSH to 192.168.86.244 as pi user
Error: Permission denied (publickey,password)
Status: Blocking deployment of vision node to hardware
```

### Resolution Options
1. **Reset RPI4-B password** (requires physical access or Pi-hole dashboard access)
2. **Add SSH public key** to RPI4-B `~/.ssh/authorized_keys` (requires current access)
3. **Use alternative deployment** (USB drive, network boot)
4. **Wait for user to provide credentials** or resolve SSH lockout

### Once SSH is Resolved
1. Run `./deploy/deploy.sh rpi4b`
2. Verify vision node running: `systemctl status pixartek-vision`
3. Test feedback messages: `mosquitto_sub -t pixartek/vision/feedback`
4. Run integration tests with real painting session
5. Perform calibration on actual setup
6. Document any hardware-specific adjustments

## Verification Checklist for Production

- [ ] Vision node running on RPI4-B
- [ ] MQTT heartbeat every 5 seconds from vision node
- [ ] Feedback published every 2 seconds while painting
- [ ] Frontend receives feedback via WebSocket
- [ ] Overlays display correctly with proper images
- [ ] Audio plays without errors
- [ ] Canvas calibration completed and accurate
- [ ] Multiple consecutive feedback messages don't overlap
- [ ] System recovers gracefully from temporary camera disconnection
- [ ] Performance: < 500ms latency from frame capture to overlay display
