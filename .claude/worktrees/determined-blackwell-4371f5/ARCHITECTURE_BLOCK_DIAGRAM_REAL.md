# PIXARTEK — Diagrama de Bloques (Block Diagram) - REAL HARDWARE

**Versión:** 3.0 (3-PI DISTRIBUTED SYSTEM)  
**Fecha:** Abril 2026  
**Estado:** Basado en Especificación Física Real  
**Fuente:** SISTEMAS DE PIXARTEK.pdf

---

## 🎯 CORE ARCHITECTURE: 3 RASPBERRY PI'S DISTRIBUTED SYSTEM

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    PIXARTEK - 3 NODE DISTRIBUTED SYSTEM                    ║
║                                                                             ║
║  NODE 1: RPI5                NODE 2: RPI4-B              NODE 3: RPI4-A    ║
║  CENTRAL ORCHESTRATOR        VISION SPECIALIST           PROJECTION DISPLAY║
║  192.168.86.243              192.168.86.245              192.168.86.244    ║
║                                                                             ║
╚════════════════════════════════════════════════════════════════════════════╝


                    ┌─────────────────────────────────────┐
                    │      NETWORK INFRASTRUCTURE         │
                    │                                     │
                    │  MQTT Broker (Mosquitto)            │
                    │  ├─ Running on RPI5:1883            │
                    │  ├─ Gigabit Ethernet                │
                    │  └─ Topics:                         │
                    │     ├─ paint/*                      │
                    │     ├─ vision/*                     │
                    │     ├─ projection/*                 │
                    │     ├─ control/*                    │
                    │     └─ system/*                     │
                    │                                     │
                    └─────────────────────────────────────┘
                           ▲        │        ▲
                           │        │        │
            ┌──────────────┘        │        └──────────────┐
            │                       │                       │
            │                       │                       │
            │                       │                       │
            ▼                       ▼                       ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   NODE 1: RPI5      │  │  NODE 2: RPI4-B     │  │  NODE 3: RPI4-A     │
│                     │  │                     │  │                     │
│  CENTRAL SYSTEM     │  │  VISION NODE        │  │  PROJECTION NODE    │
│                     │  │                     │  │                     │
│ Quad ARM64 @ 3GHz   │  │ Quad ARM64 @ 1.5GHz │  │ Quad ARM64 @ 1.5GHz │
│ 8GB LPDDR5          │  │ 4GB LPDDR4          │  │ 2GB LPDDR4          │
│ 256GB SSD           │  │ 64GB microSD        │  │ 32GB microSD        │
│                     │  │                     │  │                     │
│ RESPONSIBILITIES:   │  │ RESPONSIBILITIES:   │  │ RESPONSIBILITIES:   │
│ ├─ Orchestration    │  │ ├─ Camera capture   │  │ ├─ Image rendering  │
│ ├─ GPIO control     │  │ ├─ OpenCV analysis  │  │ ├─ HDMI output      │
│ ├─ MQTT broker      │  │ ├─ Metrics compute  │  │ ├─ Projector driver │
│ ├─ Touchscreen GUI  │  │ ├─ MQTT publisher   │  │ ├─ MQTT subscriber  │
│ └─ Hardware drivers │  │ └─ 30 FPS @ 1080p   │  │ └─ 720p @ 30 FPS    │
│                     │  │                     │  │                     │
│ CONNECTED TO:       │  │ CONNECTED TO:       │  │ CONNECTED TO:       │
│ ├─ GPIO pins        │  │ ├─ CSI Camera       │  │ ├─ Caydo P1         │
│ ├─ Motor drivers    │  │ ├─ Gigabit LAN      │  │ ├─ HDMI Display     │
│ ├─ Pump relays      │  │ └─ USB connections  │  │ └─ Gigabit LAN      │
│ ├─ Sensors/ADC      │  │                     │  │                     │
│ ├─ Touchscreen      │  │                     │  │                     │
│ ├─ HDMI display     │  │                     │  │                     │
│ └─ Gigabit LAN      │  │                     │  │                     │
│                     │  │                     │  │                     │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
        │                        │                        │
        │ GPIO CONTROL           │ MQTT                   │ MQTT
        │ (Hardware Direct)       │ (Vision Metrics)       │ (Projection Cmd)
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         HARDWARE SUBSYSTEMS                              │
│                                                                          │
│  SUBSYS #1          SUBSYS #2          SUBSYS #3       SUBSYS #4,#5    │
│  PAINT              POSITIONING        CLEANING        VISION & PROJ    │
│  DISPENSING         ACTUATOR           SYSTEM          (Remote Nodes)   │
│                                                                          │
│  [5x Pumps]         [Motor+            [Pump+           [Cameras/       │
│  [L298N #1,2]       TMC2209]           Sensor]          Projectors]     │
│  [Paint Palette]    [Linear            [Water           [Mounted on     │
│                     Actuator]          System]          RPI4-B/A]       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1. NODE 1: RPI5 - CENTRAL ORCHESTRATOR (Master)

### 1.1 Role & Responsibilities

**RPI5 is the MASTER controller that:**
- Runs the MQTT Broker (Mosquitto) for all inter-node communication
- Controls ALL hardware via GPIO pins
- Runs the touchscreen GUI application
- Coordinates the entire system workflow
- Maintains system state and timing
- Handles errors and safety shutdown

### 1.2 Hardware Specifications

```
┌─────────────────────────────────────────────────────────────┐
│         RASPBERRY PI 5 - CENTRAL ORCHESTRATOR               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ CPU:        8-core ARM Cortex-A76 @ 3.0 GHz                │
│ RAM:        8GB LPDDR5 (high-speed memory)                 │
│ Storage:    256GB SSD (via USB-C)                          │
│ Power:      USB-C PD, 5V @ 3A (15W typical)               │
│                                                              │
│ INTERFACES:                                                 │
│ ├─ GPIO Header: 40-pin standard (28 pins available)       │
│ ├─ Ethernet: Gigabit (for MQTT broker & remote PIs)       │
│ ├─ USB: 4x USB 3.0 + 2x USB-C                             │
│ ├─ HDMI: 2x Micro-HDMI (one to touchscreen)              │
│ └─ CSI: 2x CSI camera ports (optional, not used)         │
│                                                              │
│ CONNECTIVITY:                                               │
│ ├─ Ethernet IP: 192.168.1.100 (static)                   │
│ ├─ WiFi: Optional (not required for core operation)       │
│ └─ USB devices: Touch input from display                   │
│                                                              │
│ RUNNING SERVICES:                                           │
│ ├─ Mosquitto MQTT Broker (:1883)                          │
│ ├─ PyQt5 GUI Application                                   │
│ ├─ GPIO Control Thread (pumps, motor, sensors)            │
│ ├─ MQTT Listener Thread (receives from RPI4-B/A)          │
│ ├─ Sensor Polling Thread (ADC, limit switches)            │
│ ├─ Logging & Data Persistence Thread                      │
│ └─ System Monitor Thread (watchdog, safety)               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 GPIO PIN ASSIGNMENT (RPI5 → Hardware)

```
RPI5 GPIO HEADER - 40 Pin Layout:

Pin#  │ GPIO # │ Purpose                      │ Hardware Connection
──────┼────────┼──────────────────────────────┼──────────────────────────
3V3   │ ---    │ +3.3V Power Rail             │ Sensors, small logic
5V    │ ---    │ +5V Power Rail               │ Display backlight, USB
GND   │ ---    │ Ground (multiple)            │ All controllers
──────┼────────┼──────────────────────────────┼──────────────────────────
 4    │ GPIO4  │ I2C SDA (optional)           │ ADC/RTC expansion
 5    │ GPIO5  │ I2C SCL (optional)           │ ADC/RTC expansion
──────┼────────┼──────────────────────────────┼──────────────────────────
 8    │ GPIO14 │ Stepper STEP Signal          │ TMC2209 CLK pin
10    │ GPIO15 │ Stepper DIRECTION Signal     │ TMC2209 DIR pin
12    │ GPIO18 │ Stepper ENABLE               │ TMC2209 ENA pin
──────┼────────┼──────────────────────────────┼──────────────────────────
11    │ GPIO17 │ Pump #1 Control              │ L298N #1 IN1
13    │ GPIO27 │ Pump #2 Control              │ L298N #1 IN2
15    │ GPIO22 │ Pump #3 Control              │ L298N #2 IN3
16    │ GPIO23 │ Pump #4 Control              │ L298N #2 IN4
18    │ GPIO24 │ Pump #5 Emergency Solenoid   │ Solenoid valve relay
──────┼────────┼──────────────────────────────┼──────────────────────────
12    │ GPIO12 │ PWM Enable (Pump Speed)      │ L298N #1 ENA (PWM)
32    │ GPIO13 │ PWM Enable (Pump Speed)      │ L298N #2 ENB (PWM)
──────┼────────┼──────────────────────────────┼──────────────────────────
35    │ GPIO26 │ Limit Switch #1 (HOME)       │ Motor position sensor
37    │ GPIO21 │ Limit Switch #2 (END)        │ Motor position sensor
──────┼────────┼──────────────────────────────┼──────────────────────────
22    │ GPIO25 │ Cleaning Pump + Sensor       │ Submersible pump relay
                                             │ + ADC proximity sensor
──────┼────────┼──────────────────────────────┼──────────────────────────
21    │ GPIO20 │ Spare / Future use           │ Reserved for expansion
23    │ GPIO19 │ Spare / Future use           │ Reserved for expansion
──────┼────────┼──────────────────────────────┼──────────────────────────
       │        │ Reserved (UART, SPI, etc)   │ Do not use (system)
       │        │                              │
```

### 1.4 HDMI & USB Connections (RPI5)

```
┌──────────────────────────────────────────────┐
│  RPI5 External Connectors                    │
├──────────────────────────────────────────────┤
│                                              │
│  USB-C Power Input                           │
│  └─ 5V @ 3A (15W typical) from PSU          │
│                                              │
│  Micro-HDMI Port #1                          │
│  └─ → 1280x720 Touchscreen Display          │
│     └─ HDMI cable (< 2m)                    │
│     └─ USB touch input (same connector)     │
│                                              │
│  Micro-HDMI Port #2                          │
│  └─ [Not used in standard configuration]    │
│                                              │
│  Gigabit Ethernet RJ45                       │
│  ├─ IP: 192.168.1.100 (static)              │
│  ├─ → Network Switch                        │
│  ├─ → RPI4-B (Vision): 192.168.1.101       │
│  └─ → RPI4-A (Projection): 192.168.1.102   │
│                                              │
│  USB 3.0 Ports (4x)                          │
│  └─ [Reserved for future expansion]         │
│                                              │
│  USB-C Ports (2x, one for power above)       │
│  └─ One for SSD storage                     │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 2. NODE 2: RPI4-B - VISION SPECIALIST

### 2.1 Role & Responsibilities

**RPI4-B specializes in:**
- Continuous video capture from CSI camera (30 FPS)
- Real-time image analysis using OpenCV
- Canvas coverage calculation
- Color accuracy analysis
- Anomaly detection (spills, misalignment)
- Publishing metrics to MQTT broker

### 2.2 Hardware Specifications

```
┌──────────────────────────────────────────────────────────────┐
│    RASPBERRY PI 4B - VISION SPECIALIST (Slave Node #1)       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ CPU:        Quad ARM Cortex-A72 @ 1.5 GHz                   │
│ RAM:        4GB LPDDR4 (for frame buffers + processing)     │
│ Storage:    64GB microSD Card (OS + OpenCV models)          │
│ Power:      USB Micro @ 2A (10W typical)                    │
│                                                               │
│ INTERFACES:                                                  │
│ ├─ CSI Ribbon (4-lane, 1Gb/s) ← Camera Module 3             │
│ ├─ Ethernet: Gigabit (for MQTT connection to RPI5)         │
│ ├─ USB: 4x USB 3.0 (expansion capable)                     │
│ └─ HDMI: Not used                                           │
│                                                               │
│ CONNECTED HARDWARE:                                          │
│ ├─ CSI Camera Module 3 (12MP, 30 FPS @ 1080p)              │
│ │  ├─ Resolution: 4056 x 3040 pixels (native)              │
│ │  ├─ Sensor: Sony IMX708 (1/1.6")                         │
│ │  ├─ Lens: 75° FoV, fixed focus                           │
│ │  ├─ Frame Rates:                                         │
│ │  │  ├─ 30 FPS @ 1920x1080 (Full HD)                     │
│ │  │  └─ 60 FPS @ 1280x720 (HD)                           │
│ │  └─ Mounting: Adjustable angle bracket                   │
│ │     └─ Position: 1.5m above canvas, 45° angle            │
│ │                                                           │
│ └─ Gigabit Ethernet                                         │
│    └─ IP: 192.168.1.101 (static)                          │
│    └─ → MQTT Broker on RPI5:1883                           │
│                                                               │
│ RUNNING SERVICES:                                            │
│ ├─ MQTT Client (paho-mqtt)                                  │
│ ├─ OpenCV Vision Processing (asyncio)                       │
│ ├─ Frame Capture Thread (30 FPS continuous)                 │
│ ├─ Analysis Pipeline Thread                                 │
│ ├─ MQTT Publisher Thread                                    │
│ └─ Logging Thread                                           │
│                                                               │
│ SOFTWARE LIBRARIES:                                          │
│ ├─ Python 3.9+                                              │
│ ├─ OpenCV 4.5+ (image processing)                           │
│ ├─ NumPy (numerical operations)                             │
│ ├─ Pillow (image I/O)                                       │
│ ├─ paho-mqtt (MQTT client)                                  │
│ └─ asyncio (async threading)                                │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 Vision Processing Pipeline

```
CSI CAMERA (30 FPS Input)
    │
    ▼
┌─────────────────────┐
│ Frame Capture       │
│ • Continuous stream │
│ • 1920x1080 MJPEG   │
│ • Rolling buffer    │
└─────────────────────┘
    │
    ▼
┌──────────────────────┐
│ Color Space Convert  │
│ • BGR → HSV          │
│ • Separate chrominance
└──────────────────────┘
    │
    ├──────────────────────┬──────────────────┐
    │                      │                  │
    ▼                      ▼                  ▼
┌────────────┐     ┌──────────────┐  ┌──────────────┐
│ Edge Det.  │     │ Color Segm.  │  │ Contour Det. │
│ (Canny)    │     │ (Threshold)  │  │              │
└────────────┘     └──────────────┘  └──────────────┘
    │                      │                  │
    └──────────────┬───────┴──────────────────┘
                   │
                   ▼
        ┌────────────────────┐
        │ Morphology Ops     │
        │ • Dilate/Erode     │
        └────────────────────┘
                   │
                   ▼
        ┌────────────────────┐
        │ Metrics Calc       │
        │ • Coverage %       │
        │ • Color Accuracy   │
        │ • Error Detection  │
        └────────────────────┘
                   │
                   ▼
     ┌─────────────────────────┐
     │ MQTT Publish (vision/*) │
     │ ├─ vision/metrics       │
     │ ├─ vision/coverage      │
     │ └─ vision/errors        │
     └─────────────────────────┘

Output to RPI5 via MQTT Broker (:1883)
```

---

## 3. NODE 3: RPI4-A - PROJECTION SPECIALIST

### 3.1 Role & Responsibilities

**RPI4-A specializes in:**
- Receiving projection commands via MQTT
- Loading stage-specific guide images
- Rendering to HDMI @ 720p, 30 FPS
- Controlling Caydo P1 projector display
- Updating visual guides in real-time

### 3.2 Hardware Specifications

```
┌──────────────────────────────────────────────────────────────┐
│  RASPBERRY PI 4A - PROJECTION SPECIALIST (Slave Node #2)     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ CPU:        Quad ARM Cortex-A72 @ 1.5 GHz                   │
│ RAM:        2GB LPDDR4 (frame buffers + image cache)        │
│ Storage:    32GB microSD Card (OS + guide images)           │
│ Power:      USB Micro @ 2A (8W typical)                     │
│                                                               │
│ INTERFACES:                                                  │
│ ├─ HDMI: Full-size HDMI (→ Caydo P1 Projector)             │
│ ├─ Ethernet: Gigabit (for MQTT connection to RPI5)         │
│ ├─ USB: 4x USB 3.0 (expansion capable)                     │
│ └─ CSI: Not used (this is RPI4A variant)                    │
│                                                               │
│ CONNECTED HARDWARE:                                          │
│ ├─ Caydo P1 LED Projector                                   │
│ │  ├─ Brightness: 200 ANSI Lumens                           │
│ │  ├─ Resolution: 720p (1280x720)                           │
│ │  ├─ Contrast: 1000:1                                      │
│ │  ├─ Throw Distance: 0.3-2m (adjustable)                   │
│ │  ├─ Keystone: ±15° (software corrected)                   │
│ │  ├─ Light Source: LED (50,000h lifespan)                  │
│ │  ├─ Input: HDMI only                                      │
│ │  └─ Power: 5V/2A USB (via HDMI power adapter)             │
│ │                                                           │
│ └─ Gigabit Ethernet                                         │
│    └─ IP: 192.168.1.102 (static)                          │
│    └─ → MQTT Broker on RPI5:1883                           │
│                                                               │
│ RUNNING SERVICES:                                            │
│ ├─ MQTT Client (paho-mqtt)                                  │
│ ├─ PyGame Rendering Engine                                  │
│ ├─ HDMI Output Thread (30 FPS)                              │
│ ├─ MQTT Subscriber Thread                                   │
│ ├─ Image Loader Thread                                      │
│ └─ Logging Thread                                           │
│                                                               │
│ SOFTWARE LIBRARIES:                                          │
│ ├─ Python 3.9+                                              │
│ ├─ PyGame 2.1+ (graphics & rendering)                       │
│ ├─ Pillow (image loading)                                   │
│ ├─ paho-mqtt (MQTT client)                                  │
│ └─ asyncio (async threading)                                │
│                                                               │
│ ASSET LIBRARY (on microSD):                                  │
│ └─ ~/projection/images/                                     │
│    ├─ stage_1_guide.png (outline + color1 zones)           │
│    ├─ stage_2_guide.png (color2 zones)                     │
│    ├─ ... up to 10 stages ...                              │
│    ├─ ui_overlays/                                         │
│    │  ├─ stage_number.png                                  │
│    │  ├─ color_indicator.png                               │
│    │  └─ progress_bar.png                                  │
│    └─ error_screens/                                       │
│       ├─ system_paused.png                                 │
│       ├─ error_detected.png                                │
│       └─ cleanup_mode.png                                  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 3.3 Projection Rendering Pipeline

```
MQTT Subscribe (projection/cmd)
    │
    ▼
┌─────────────────────┐
│ Parse Command       │
│ • Decode stage #    │
│ • Extract color     │
│ • Extract duration  │
└─────────────────────┘
    │
    ▼
┌──────────────────────┐
│ Load Image File      │
│ from ~/images/       │
│ (PNG with alpha)     │
└──────────────────────┘
    │
    ▼
┌────────────────────────┐
│ Render to Buffer       │
│ • 1280x720 resolution  │
│ • Apply color tint     │
│ • Add text overlay     │
│ • Apply keystone corr. │
└────────────────────────┘
    │
    ▼
┌────────────────────────┐
│ Output to HDMI         │
│ • 30 FPS continuous    │
│ • To Caydo P1 projector│
└────────────────────────┘
    │
    ▼
  CANVAS (Projected Visual Guide)
```

---

## 4. INTER-NODE COMMUNICATION DIAGRAM

### 4.1 MQTT Message Flow

```
╔════════════════════════════════════════════════════════════════╗
║         MQTT BROKER (Mosquitto - Running on RPI5)              ║
║                 192.168.1.100:1883                             ║
╚════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  Topics & Publishers/Subscribers:                               │
│                                                                   │
│  paint/dispense                                                  │
│  ├─ Publisher: RPI5 GUI (user selects color)                    │
│  └─ Subscriber: RPI5 Hardware Thread (executes pump control)    │
│                                                                   │
│  paint/position                                                  │
│  ├─ Publisher: RPI5 GUI (position actuator)                     │
│  └─ Subscriber: RPI5 Hardware Thread (execute motor steps)      │
│                                                                   │
│  paint/status                                                    │
│  ├─ Publisher: RPI5 Hardware Thread (pump complete)             │
│  └─ Subscriber: RPI5 GUI (update display)                       │
│                                                                   │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│                                                                   │
│  vision/metrics                                                  │
│  ├─ Publisher: RPI4-B Vision Thread (every 100ms)               │
│  └─ Subscriber: RPI5 GUI (real-time feedback display)           │
│                                                                   │
│  vision/coverage                                                 │
│  ├─ Publisher: RPI4-B (canvas % painted)                        │
│  └─ Subscriber: RPI5 GUI                                        │
│                                                                   │
│  vision/errors                                                   │
│  ├─ Publisher: RPI4-B (anomalies detected)                      │
│  └─ Subscriber: RPI5 GUI (alert user)                           │
│                                                                   │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│                                                                   │
│  projection/cmd                                                  │
│  ├─ Publisher: RPI5 (stage change, color selection)             │
│  └─ Subscriber: RPI4-A Rendering Thread (update display)        │
│                                                                   │
│  projection/status                                               │
│  ├─ Publisher: RPI4-A (rendering complete, latency)             │
│  └─ Subscriber: RPI5 GUI (confirm projection updated)           │
│                                                                   │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│                                                                   │
│  control/emergency                                               │
│  ├─ Publisher: RPI5 GUI (user presses STOP)                     │
│  └─ Subscriber: RPI4-B, RPI4-A (pause operations)               │
│                                                                   │
│  system/status                                                   │
│  ├─ Publisher: All nodes (heartbeat, health check)              │
│  └─ Subscriber: All nodes (monitor node connectivity)           │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Timing & Latency

```
LATENCY BUDGET - End-to-End Communication:

Touch Input (RPI5 GUI)
    │ ~10ms
    ▼
GUI Processing
    │ ~20ms
    ▼
MQTT Publish paint/dispense
    │ ~10ms
    ▼
Network transmission
    │ ~20ms
    ▼
MQTT Broker delivery
    │ ~5ms
    ▼
RPI5 Hardware Thread receives
    │ ~5ms
    ▼
GPIO control signal (pump activates)
    │ HARDWARE RESPONSE: ~100ms
    ▼
Paint flowing
    │ Vision capture starts
    ▼
RPI4-B processes frame
    │ ~45ms
    ▼
MQTT Publish vision/metrics
    │ ~30ms
    ▼
RPI5 receives metrics
    │ ~10ms
    ▼
GUI updates display
    │ ~20ms
    ▼
USER SEES FEEDBACK: ~300-400ms ✓ Acceptable

Total E2E Latency: ~300-400ms (human perception threshold ~150-200ms)
```

---

## 5. GPIO CONTROL - DIRECT RPI5 → HARDWARE

```
RPI5 GPIO PINS (Direct Hardware Control - NOT via MQTT):

┌──────────────────────────────────────────────────────────────────┐
│                    SUBSYSTEM 1: PAINT DISPENSING                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  GPIO17 (Pin 11) → L298N #1 IN1 → Pump #1 (Red)                │
│  GPIO27 (Pin 13) → L298N #1 IN2 → Pump #2 (Blue)               │
│  GPIO22 (Pin 15) → L298N #2 IN3 → Pump #3 (Yellow)             │
│  GPIO23 (Pin 16) → L298N #2 IN4 → Pump #4 (Green)              │
│  GPIO24 (Pin 18) → Solenoid Valve → Pump #5 (Custom)           │
│                                                                   │
│  GPIO12 (Pin 32) → L298N #1 ENA (PWM) → Speed Control #1,#2    │
│  GPIO13 (Pin 33) → L298N #2 ENB (PWM) → Speed Control #3,#4    │
│                                                                   │
│  Voltage: 3.3V GPIO → 12V Motor drivers (via relay/optoisolator)
│  Current: <25mA per GPIO pin                                      │
│  Frequency: 1-10 kHz for PWM speed control                        │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                   SUBSYSTEM 2: POSITIONING MOTOR                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  GPIO14 (Pin 8) → TMC2209 CLK → Step Pulses                     │
│  GPIO15 (Pin 10) → TMC2209 DIR → Direction Control             │
│  GPIO18 (Pin 12) → TMC2209 ENA → Motor Enable/Disable          │
│                                                                   │
│  GPIO26 (Pin 35) ← Limit Switch #1 (HOME/START)                │
│  GPIO21 (Pin 37) ← Limit Switch #2 (END)                       │
│                                                                   │
│  Voltage: 3.3V GPIO ↔ 5V TMC2209 logic (with level shifter)    │
│  Step Rate: 1-2 kHz for smooth motion                            │
│  Current: <25mA per GPIO pin                                      │
│                                                                   │
│  TMC2209 Stepper Driver:                                         │
│  ├─ Logic: 3.3V (from RPI5 with level shifter)                 │
│  ├─ Power: 12V supply (separate from GPIO)                      │
│  ├─ Motor: NEMA17 Stepper (4-wire bipolar)                     │
│  └─ Microstepping: 1/16 mode (18.75µm resolution)              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    SUBSYSTEM 3: CLEANING SYSTEM                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  GPIO25 (Pin 22) → Cleaning Pump Relay                          │
│  GPIO25 (Pin 22) ← Proximity Sensor ADC input                   │
│                                                                   │
│  Proximity Sensor (Sharp GP2Y0A41SK0F):                          │
│  ├─ Analog output: 0-3.3V (distance 0-30cm)                    │
│  ├─ ADC Input: Via MCP3008 (SPI) or native ADC                 │
│  └─ Sampling: 200ms polling interval                             │
│                                                                   │
│  Submersible Pump:                                               │
│  ├─ 12V power (via relay)                                        │
│  ├─ Control: GPIO HIGH (on) / LOW (off)                         │
│  └─ Current: ~1A (relay rated for 2A)                            │
│                                                                   │
│  Voltage: 3.3V GPIO ↔ 12V Pump relay                            │
│  Current: <25mA per GPIO pin                                      │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. POWER DISTRIBUTION SYSTEM

### 6.1 Power Supply Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                    AC POWER INPUT (110V Wall)                      │
└────────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
        ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
        │ 5V PSU      │ │12V PSU #1   │ │ 12V PSU #2   │
        │ 3A (15W)    │ │ 8A (96W)    │ │ 8A (96W)     │
        └─────────────┘ └─────────────┘ └──────────────┘
            │               │               │
            └───────────────┼───────────────┘
                            │
                            ▼
        ┌────────────────────────────────────────────┐
        │   POWER DISTRIBUTION BOARD                 │
        │   (Fused & Protected Outputs)              │
        └────────────────────────────────────────────┘
            │       │         │          │
            │       │         │          │
    ┌───────┘       │         │          └────────┐
    │               │         │                   │
    ▼               ▼         ▼                   ▼
5V Outputs      12V Outputs (Pumps)    12V Motor  12V Backups
├─RPI5:3A       ├─L298N #1: 2A        │          │
├─RPI4-B:2A     ├─L298N #2: 2A        ▼          ▼
├─RPI4-A:2A     ├─TMC2209: 1.5A   [Stepper]  [Spare Relays]
├─Display:1A    └─Pump Clean: 1A
└─Projector:2A


COMPONENT POWER DRAW:
┌──────────────────────────────────────────────────────┐
│ Component              │ Voltage │ Current │ Power    │
├────────────────────────┼─────────┼─────────┼──────────┤
│ RPI5 (CPU + System)    │ 5V      │ 3A max  │ 15W      │
│ RPI4-B (Vision Proc)   │ 5V      │ 2A max  │ 10W      │
│ RPI4-A (Projection)    │ 5V      │ 2A max  │ 10W      │
│ Touchscreen Display    │ 5V      │ 1A      │ 5W       │
│ Caydo P1 Projector     │ 5V      │ 2A      │ 10W      │
├────────────────────────┼─────────┼─────────┼──────────┤
│ 5V TOTAL               │ ---     │ 10A     │ 50W      │
├────────────────────────┼─────────┼─────────┼──────────┤
│ Peristaltic Pump #1    │ 12V     │ 1A      │ 12W      │
│ Peristaltic Pump #2    │ 12V     │ 1A      │ 12W      │
│ Peristaltic Pump #3    │ 12V     │ 1A      │ 12W      │
│ Peristaltic Pump #4    │ 12V     │ 1A      │ 12W      │
│ Peristaltic Pump #5    │ 12V     │ 0.5A    │ 6W       │
│ Submersible Pump       │ 12V     │ 0.8A    │ 10W      │
│ NEMA17 Stepper Motor   │ 12V     │ 1.2A    │ 14W      │
├────────────────────────┼─────────┼─────────┼──────────┤
│ 12V TOTAL (All loads)  │ ---     │ 7.5A    │ 90W      │
├────────────────────────┼─────────┼─────────┼──────────┤
│ SYSTEM PEAK DRAW       │ ---     │ ---     │ 140W     │
│ SYSTEM NOMINAL         │ ---     │ ---     │ 80W      │
└──────────────────────────────────────────────────────┘
```

### 6.2 Fusing & Protection

```
FUSE LOCATIONS:

5V PSU Output:
├─ Main Fuse: 10A @ 5V input (emergency cutoff)
├─ Branch to RPI5: 5A fuse
├─ Branch to Peripherals: 5A fuse (displays, projector)
└─ Branch Reserve: 2A fuse (future expansion)

12V PSU #1 Output (Pumps):
├─ Main Fuse: 15A @ 12V input
├─ L298N #1: 5A fuse (2 pump motors)
├─ L298N #2: 5A fuse (2 pump motors)
└─ Reserve: 5A fuse

12V PSU #2 Output (Motors & Cleaning):
├─ Main Fuse: 15A @ 12V input
├─ TMC2209: 3A fuse (stepper motor)
├─ Cleaning: 2A fuse (submersible + solenoid)
└─ Reserve: 10A fuse

PROTECTION FEATURES:
├─ Thermal overload protection (in each PSU)
├─ Over-voltage clamp (Zener diodes on 5V & 12V rails)
├─ Isolation optocouplers (GPIO to motor driver inputs)
├─ Bypass capacitors (100µF + 0.1µF on each power rail)
└─ Separate ground plane (noise immunity)
```

---

## 7. PHYSICAL LAYOUT & WIRING

```
TOP VIEW - Complete System Placement:

                    FRONT (User Area)
   ┌────────────────────────────────────────────────────┐
   │                    PROJECTOR CAYDO P1              │  1.5m
   │              ▲ (mounted 0.5m above canvas)        │  high
   │              │ (RPI4-A control)                   │
   │              │                                    │
   │ ┌─────────────────────────────────┐              │
   │ │                                 │              │
   │ │        CANVAS (1000x800mm)      │              │
   │ │      (painting surface)         │              │
   │ │                                 │              │
   │ │  ▼ CSI Camera                   │              │
   │ │  (RPI4-B, 1.5m above)           │              │
   │ │  (45° angle)                    │              │
   │ │                                 │              │
   │ │  [PAINT PALETTE]                │              │
   │ │  [6 Compartments]               │              │
   │ │  ↑ Nozzle above (actuator)      │              │
   │ │                                 │              │
   │ │  [CLEANING STATION]             │              │
   │ │  (30cm right of canvas)         │              │
   │ │   Proximity Sensor             │              │
   │ │   Shower Hose                   │              │
   │ │                                 │              │
   │ └─────────────────────────────────┘              │
   │                                                   │
   │ ┌──────────────────────────────────┐            │
   │ │ RPI5 + TOUCHSCREEN (7-10")       │            │
   │ │ (GUI Control - Front of table)   │            │
   │ │ 1280x720 display                 │            │
   │ └──────────────────────────────────┘            │
   │                                                   │
   │ ┌──────────────────────────────────┐            │
   │ │ POWER DISTRIBUTION BOARD         │            │
   │ │ & Motor Drivers (under table)    │            │
   │ │ • L298N #1, #2                   │            │
   │ │ • TMC2209                        │            │
   │ │ • PSU 5V, 12V #1, 12V #2         │            │
   │ │ • Fuses & Protection             │            │
   │ └──────────────────────────────────┘            │
   │                                                   │
   │ ┌──────────────────────────────────┐            │
   │ │ NETWORK SWITCH (Gigabit)         │            │
   │ │ RPI5 ↔ RPI4-B ↔ RPI4-A          │            │
   │ │ (Ethernet cables, < 2m)          │            │
   │ └──────────────────────────────────┘            │
   │                                                   │
   └────────────────────────────────────────────────┘
                  BACK (Control Area)


CABLE ROUTING:

RPI5 GPIO → Motor Drivers
├─ 5-pin cable (GPIO17,27,22,23,24)
├─ 2-pin PWM cable (GPIO12,13)
├─ 3-pin stepper cable (GPIO14,15,18)
├─ 3-pin limit switches (GPIO26,21 + GND)
└─ 2-pin cleaning pump (GPIO25 + GND)

RPI5 → Touchscreen
├─ HDMI cable (< 2m)
├─ USB touch data cable
└─ 5V power (USB-C)

RPI4-B ↔ Network
├─ Gigabit Ethernet (RJ45)
└─ 5V USB Micro power

RPI4-A ↔ Projector
├─ HDMI cable (< 2m)
├─ Gigabit Ethernet (RJ45)
└─ 5V USB Micro power (shared with USB adapter to projector)

CSI Camera → RPI4-B
└─ 4-lane CSI ribbon (< 1m, shielded)
```

---

## 8. NODE INTERACTION SUMMARY TABLE

```
┌──────────────┬──────────────┬──────────────────────┬──────────────────┐
│ NODE         │ IP Address   │ Key Responsibility   │ Connected Devices│
├──────────────┼──────────────┼──────────────────────┼──────────────────┤
│              │              │                      │                  │
│ RPI5         │ .100         │ • Central orchestrat.│ • 40 GPIO pins   │
│ (Master)     │ (static)     │ • MQTT Broker        │ • Touchscreen    │
│              │              │ • GUI touchscreen    │ • 2x HDMI output │
│              │              │ • GPIO control       │ • Gigabit LAN    │
│              │              │ • Safety & Timing    │ • Power: 5V USB-C│
│              │              │                      │                  │
├──────────────┼──────────────┼──────────────────────┼──────────────────┤
│              │              │                      │                  │
│ RPI4-B       │ .101         │ • Vision processing  │ • CSI Camera     │
│ (Slave #1)   │ (static)     │ • Metrics compute    │ • Gigabit LAN    │
│              │              │ • Frame capture 30FPS│ • Power: 5V µUSB │
│              │              │ • MQTT publisher     │                  │
│              │              │                      │                  │
├──────────────┼──────────────┼──────────────────────┼──────────────────┤
│              │              │                      │                  │
│ RPI4-A       │ .102         │ • Projection control │ • Caydo P1       │
│ (Slave #2)   │ (static)     │ • HDMI rendering     │ │  Projector     │
│              │              │ • Image loading      │ • HDMI output    │
│              │              │ • MQTT subscriber    │ • Gigabit LAN    │
│              │              │ • 720p @ 30 FPS      │ • Power: 5V µUSB │
│              │              │                      │                  │
└──────────────┴──────────────┴──────────────────────┴──────────────────┘
```

---

## 9. CONCLUSION: 3-PI ARCHITECTURE

This is a **distributed 3-node system** where:

- **RPI5 (Node 1):** Central hub - orchestrates all operations, controls hardware via GPIO, hosts MQTT broker, GUI
- **RPI4-B (Node 2):** Vision specialist - captures video, analyzes canvas, publishes metrics
- **RPI4-A (Node 3):** Projection specialist - receives commands, renders guides, displays on projector

All inter-node communication happens through **MQTT**, all hardware control through **GPIO**, all real-time feedback through **MQTT topics**.

This separation allows each node to specialize in its function while remaining loosely coupled through the message broker.

---

**Fin de Architecture Block Diagram - 3 PI Distributed System**
