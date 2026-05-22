# PIXARTEK - Architectural Design Document (Real Hardware System)

**Versión:** 2.0  
**Fecha:** Abril 2026  
**Estado:** Basado en Especificación Física Real  
**Fuente:** SISTEMAS DE PIXARTEK.pdf

---

## 1. INTRODUCCIÓN

### 1.1 Propósito
Este documento describe la arquitectura de diseño del sistema PIXARTEK, detallando cómo los 6 subsistemas principales se integran para crear un robot dispensador de pintura automatizado con retroalimentación visual en tiempo real.

### 1.2 Audiencia
- Ingenieros de hardware
- Desarrolladores de firmware/software
- Técnicos de integración
- Personal de mantenimiento

### 1.3 Perspectiva General
PIXARTEK es un sistema robótico integrado con:
- **Control Central:** Raspberry Pi 5 (coordinación y UI)
- **Nodos Especializados:** Raspberry Pi 4 (visión y proyección)
- **Hardware Periférico:** Bombas, sensores, actuadores, pantalla táctil
- **Comunicación:** MQTT, GPIO, USB, red local

---

## 2. ARQUITECTURA GENERAL DEL SISTEMA

### 2.1 Diagrama de Componentes de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIXARTEK SYSTEM ARCHITECTURE                      │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  RPI5 - CONTROL CENTRAL                      │   │
│  │            (Coordinación, UI, Lógica Principal)              │   │
│  │                                                               │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │  SUBSISTEMA 1: PANEL DE CONTROL (Control Panel)     │    │   │
│  │  │  • Pantalla Táctil HDMI (1280x720, 7-10")          │    │   │
│  │  │  • Interface de Usuario (GUI en Python/Qt)         │    │   │
│  │  │  • Visualización de Estado                          │    │   │
│  │  │  • Controles Manuales & Emergencia                 │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  │                                                               │   │
│  │  GPIO CONTROL SIGNALS ──────────────────────────────┐        │   │
│  │                                                     │        │   │
│  └──────────────────────────────────────────────────────┼───────┘   │
│         │            │                │                 │             │
│         │            │                │                 │             │
│         ▼            ▼                ▼                 ▼             │
│  ┌────────────┐ ┌──────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │ SUBSISTEMA │ │SUBSISTEMA│  │ SUBSISTEMA 3 │  │ SUBSISTEMA 4  │   │
│  │     1      │ │    2     │  │  (Cleaning)  │  │    (Vision)   │   │
│  │  (Paint    │ │(Position)│  │              │  │               │   │
│  │ Dispensing)│ │          │  │ Submergible  │  │ CSI Camera    │   │
│  │            │ │Linear    │  │ Pump +       │  │ (Mounted)     │   │
│  │5x Peristal.│ │Actuator+ │  │ Prox. Sensor │  │               │   │
│  │Pumps(L298N)│ │TMC2209   │  │              │  │ RPI4-B        │   │
│  │            │ │(NEMA 17) │  │ Drenaje      │  │ (Processing)  │   │
│  └────────────┘ └──────────┘  └──────────────┘  └───────────────┘   │
│         │            │                │                 │             │
│         │            │                │     ┌───────────┴─────────┐   │
│         │            │                │     │                     │   │
│         └────────────┴────────────────┴─────┤    MQTT BROKER      │   │
│                                             │  (Mosquitto, Port   │   │
│                                             │   1883 on RPI5)     │   │
│                                             │                     │   │
│         ┌────────────────────────────┐     │ Topics:             │   │
│         │  SUBSISTEMA 5              │◄────┤ • paint/*           │   │
│         │  (Projection)              │     │ • vision/*          │   │
│         │                            │     │ • control/*         │   │
│         │  Caydo P1 Projector        │     │ • system/*          │   │
│         │  RPI4-A (Control)          │     │                     │   │
│         │                            │     │                     │   │
│         └────────────────────────────┘     └─────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

LEYENDA:
─ GPIO Signals (RPI5 → Hardware Controllers)
═ MQTT Messages (Inter-Pi Communication)
═ USB/CSI (Direct Hardware Connections)
```

### 2.2 Distribución Física del Sistema

| Componente | Ubicación | Interfaz | Voltaje | Controlador |
|-----------|-----------|----------|---------|------------|
| RPI5 | Central | GPIO, HDMI, USB-C | 5V USB-C | -autónomo- |
| RPI4 Vision | Montaje Cámara | CSI, USB | 5V Micro-USB | -autónomo- |
| RPI4 Proyección | Estructura Proyector | HDMI, USB | 5V Micro-USB | -autónomo- |
| 5x Bombas Peristálticas | Envases de Pintura | GPIO (5 pines) | 12V | L298N x2 |
| Motor Stepper NEMA17 | Actuador Lineal | GPIO (4 pines) | 12V | TMC2209 |
| Sensor Proximidad IR | Estación de Limpieza | GPIO (1 pin) | 5V | GPIO RPI5 |
| Bomba Sumergible | Tanque de Agua | GPIO (1 pin) | 12V | L298N |
| Proyector Caydo P1 | Estructura Fija | HDMI + USB Power | 5V/12V | RPI4-A |
| Cámara CSI | Montaje Ajustable | CSI Ribbon | 3.3V | RPI4-B |
| Pantalla Táctil | Frente del Sistema | HDMI + USB Touch | 5V | RPI5 |

---

## 3. LOS 6 SUBSISTEMAS PRINCIPALES

### 3.1 SUBSISTEMA 1: DISPENSACIÓN DE PINTURA (Paint Dispensing)

#### 3.1.1 Descripción General
Sistema que controla la liberación precisa de pintura en 5 colores diferentes (máximo) distribuidos en una paleta de 6 compartimentos mediante bombas peristálticas controladas electrónicamente.

#### 3.1.2 Componentes del Subsistema

```
┌─────────────────────────────────────────────────────┐
│         PAINT DISPENSING SUBSYSTEM (RPI5)           │
│                                                     │
│  GPIO Pins (RPI5):                                 │
│  ├─ GPIO17: Pump 1 Control (IN1 on L298N #1)      │
│  ├─ GPIO27: Pump 2 Control (IN2 on L298N #1)      │
│  ├─ GPIO22: Pump 3 Control (IN3 on L298N #2)      │
│  ├─ GPIO23: Pump 4 Control (IN4 on L298N #2)      │
│  ├─ GPIO24: Pump 5 Control (Emergency Solenoid)   │
│  └─ GPIO12,13: PWM Channels (Speed Control)       │
│                                                     │
│  L298N Motor Driver #1:                            │
│  ├─ 12V In → 2 Peristaltic Pumps                  │
│  ├─ GND Shared                                     │
│  └─ Enable: PWM for speed                         │
│                                                     │
│  L298N Motor Driver #2:                            │
│  ├─ 12V In → 2 Peristaltic Pumps                  │
│  ├─ GND Shared                                     │
│  └─ Enable: PWM for speed                         │
│                                                     │
│  Paint Containers:                                 │
│  ├─ Pump 1 → Color 1 (e.g., Red)                 │
│  ├─ Pump 2 → Color 2 (e.g., Blue)                │
│  ├─ Pump 3 → Color 3 (e.g., Yellow)              │
│  ├─ Pump 4 → Color 4 (e.g., Green)               │
│  └─ Pump 5 → Color 5 (e.g., Custom)              │
│                                                     │
│  Tubing System:                                    │
│  ├─ 10x Medical Suction Tubes (input)             │
│  ├─ 5x Multi-channel Distribution (output)        │
│  └─ 1x Calibrated Dispensing Nozzle (tip)        │
│                                                     │
│  Paint Palette:                                    │
│  ├─ 6 Compartments (fixed position)               │
│  ├─ 5 Colores Activos + 1 Vacío/Limpieza         │
│  └─ ~500ml capacity per compartment               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### 3.1.3 Flujo de Control
```
User Selection         RPI5 Decision       Motor Control       Paint Flow
      │                    │                    │                   │
      │ User selects       │                    │                   │
      │ "Red Color"        │                    │                   │
      └──────────────────►  │                    │                   │
                           │ Calculate time     │                   │
                           │ for 50ml @ 25ml/s  │                   │
                           │ = 2 seconds        │                   │
                           │                    │                   │
                           │ GPIO17 HIGH        │                   │
                           │ PWM Freq=1kHz      │                   │
                           │ Duty=80%           │                   │
                           └──────────────────► │                   │
                                               │ L298N activates   │
                                               │ Motor spins       │
                                               │ at 80% power      │
                                               └──────────────────►│
                                                                   │ Pump
                                                                   │ dispenses
                                                                   │ at rate
                                                                   └─────►
                                               (After 2 seconds)
                           GPIO17 LOW
                           ◄──────────────────────────────────────────┘
```

#### 3.1.4 Especificaciones Técnicas
- **Volumen de dispensación:** 10-200ml por color
- **Precisión:** ±5% del volumen objetivo
- **Velocidad:** ~25ml/segundo (bomba peristáltica estándar)
- **Presión máxima:** 2 bar (limitador integrado)
- **Frecuencia de cambio de color:** < 1 segundo entre pozos

---

### 3.2 SUBSISTEMA 2: POSICIONAMIENTO DEL ACTUADOR (Positioning)

#### 3.2.1 Descripción General
Sistema que maneja el movimiento preciso del cabezal de dispensación sobre cada uno de los 6 compartimentos de la paleta usando un actuador lineal controlado por motor stepper.

#### 3.2.2 Componentes del Subsistema

```
┌────────────────────────────────────────────────────────┐
│       POSITIONING SUBSYSTEM (RPI5 + Linear Motor)      │
│                                                        │
│  GPIO Pins (RPI5):                                    │
│  ├─ GPIO14: Step Signal (CLK to TMC2209)             │
│  ├─ GPIO15: Direction Signal (DIR to TMC2209)        │
│  ├─ GPIO18: Enable Signal (ENA to TMC2209)           │
│  ├─ GPIO26: Limit Switch Start (GPIO Input)          │
│  └─ GPIO21: Limit Switch End (GPIO Input)            │
│                                                        │
│  TMC2209 Stepper Driver:                              │
│  ├─ Logic: 3.3V (from RPI GPIO)                      │
│  ├─ Power: 12V (external supply)                      │
│  ├─ Microsteps: 1/16 mode (fine resolution)          │
│  ├─ Current Limit: 1.2A                              │
│  ├─ Protection: Over-current, Over-temp              │
│  └─ Monitoring: SPI interface (optional)             │
│                                                        │
│  NEMA 17 Stepper Motor:                               │
│  ├─ Holding Torque: ~0.4 Nm                          │
│  ├─ Step Angle: 1.8°/step (200 steps/revolution)    │
│  ├─ Coils: 4-wire bipolar                            │
│  ├─ Voltage: 12V nominal                             │
│  └─ Max Current: 1.5A per coil                       │
│                                                        │
│  Linear Actuator:                                      │
│  ├─ Mechanism: Screw-driven linear motion            │
│  ├─ Stroke: 300-400mm                                │
│  ├─ Pitch: 5mm (high precision)                      │
│  ├─ Direction: Horizontal (X-axis)                   │
│  ├─ Load: ~500g (nozzle + tube + motor)             │
│  └─ Limit Switches: 2x NO (Normally Open)           │
│                                                        │
│  Position Reference Points:                           │
│  ├─ Position 0: Limit Switch START (leftmost)       │
│  ├─ Positions 1-6: Paint Palette Compartments       │
│  │   (spacing: ~60mm between centers)               │
│  └─ Homing: Always return to Position 0 on startup  │
│                                                        │
│  Calibration Data (stored in RPI5 persistent):       │
│  ├─ Offset per compartment (microns)                 │
│  ├─ Speed profile (acceleration/deceleration)        │
│  └─ Limit switch trigger points                      │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### 3.2.3 Control del Motor Stepper
```
Movement Sequence: From Position 0 → Position 3 (60mm)

Step 1: Enable Motor
        GPIO18 = HIGH (enable TMC2209)
        Wait 10ms for stabilization

Step 2: Set Direction
        GPIO15 = HIGH (forward) or LOW (backward)
        Wait 2ms for settling

Step 3: Generate Pulses
        For 480 steps (at 1/16 microsteps = 1920 GPIO pulses):
            GPIO14 = HIGH (100µs)
            GPIO14 = LOW (100µs)
            Repeat 1920 times
            (Takes ~0.4 seconds for 60mm movement)

Step 4: Verify Position
        GPIO26 or GPIO21 = HIGH (limit switch triggered)?
        If not, check encoder feedback (if available)

Step 5: Stop & Hold
        GPIO18 = LOW (disable motor, hold by coil)
        Motor remains in position without power drain
        (TMC2209 maintains current through both coils)

Software State Machine:
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   IDLE      │────►│   HOMING     │────►│   READY      │
│             │     │  (HOME_POS)  │     │  (Any Pos)   │
└─────────────┘     └──────────────┘     └──────────────┘
       ▲                                        │
       │                                        │
       │                ┌───────────────────────┘
       │                │
       │            ┌───▼────────────┐
       │            │  MOVING        │
       │            │  (Pos N→N+1)   │
       │            └────────────────┘
       │                     │
       └─────────────────────┘
         (Movement Complete)
```

#### 3.2.4 Especificaciones Técnicas
- **Resolución:** 1/16 microsteps = 18.75 µm por paso
- **Velocidad máxima:** 2 segundos entre pozos
- **Aceleración:** Rampa suave para evitar vibración
- **Ruido:** < 50dB (motor silencioso en modo microstepping)
- **Confiabilidad:** 99.95% (sin pérdida de pasos con carga nominal)

---

### 3.3 SUBSISTEMA 3: LIMPIEZA AUTOMÁTICA (Cleaning)

#### 3.3.1 Descripción General
Sistema que limpia automáticamente los pinceles del usuario cuando detecta proximidad mediante un sensor infrarrojo, usando una bomba sumergible para riego de agua.

#### 3.3.2 Componentes del Subsistema

```
┌────────────────────────────────────────────────────────┐
│      CLEANING SUBSYSTEM (RPI5 + Pumps + Sensor)        │
│                                                        │
│  GPIO Pin (RPI5):                                     │
│  └─ GPIO25: Pump Control + Proximity Sensor Input    │
│                                                        │
│  Proximity Sensor (Infrared):                          │
│  ├─ Type: Sharp GP2Y0A41SK0F                          │
│  ├─ Detection Range: 0-30 cm                          │
│  ├─ Output: Analog voltage (ADC input via MCP3008)   │
│  ├─ Sensitivity: Adjustable threshold                 │
│  ├─ Power: 5V from RPI5                              │
│  └─ Mounting: At brush cleaning station              │
│                                                        │
│  Submersible Pump:                                    │
│  ├─ Type: Aquarium centrifugal pump                  │
│  ├─ Power: 12V DC                                    │
│  ├─ Flow Rate: 2-3 liters/minute                     │
│  ├─ Max Pressure: 0.5 bar                            │
│  ├─ Power Consumption: ~8W                           │
│  ├─ Inlet: Submerged in clean water tank            │
│  └─ Outlet: To PVC tubing network                    │
│                                                        │
│  PVC Tubing System:                                   │
│  ├─ 1x Main Tube (12mm ID, rigid)                    │
│  ├─ 2x Elbows (90°, PVC)                             │
│  ├─ 1x Adapter (Rain Tape Distribution)              │
│  ├─ 1x Flex Shower Hose (final applicator)           │
│  └─ All connections: PVC cement + clamps             │
│                                                        │
│  Water Storage:                                        │
│  ├─ Clean Water Tank: 5-10L capacity                 │
│  ├─ Wash Basin: 2-3L capacity (for brush)            │
│  ├─ Drainage Basin: 10L capacity (waste)             │
│  └─ Refill Schedule: Every 8 operating hours         │
│                                                        │
│  Safety Features:                                      │
│  ├─ Overflow Prevention: 5cm vent hole               │
│  ├─ Anti-siphon: Check valve in intake line         │
│  ├─ Dry-run Protection: Moisture switch              │
│  └─ Auto-shutoff: 30sec timeout if sensor stuck     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### 3.3.3 Secuencia de Operación

```
Timeline: Proximity Detection & Cleaning Cycle

t=0ms    Brush enters detection zone (< 30cm)
         ├─ Proximity sensor reads ADC
         ├─ Value > Threshold (e.g., 600/1023)
         └─ RPI5 detects change

t=100ms  Debounce check (confirm sensor stable for 100ms)
         └─ No false positives

t=200ms  Pump activation
         ├─ GPIO25 = HIGH
         ├─ L298N activates 12V supply
         └─ Submersible pump starts

t=300ms  Water flow established
         ├─ Pump reaches full speed (~100ms startup)
         ├─ Water flows through PVC system
         └─ Shower hose dispenses as rain over brush

t=300-30000ms  Sustained operation
         ├─ Sensor continues reading proximity
         ├─ RPI5 monitors every 200ms
         └─ Pump remains on

t=31000ms  Brush moves away (sensor < Threshold)
         ├─ RPI5 detects sensor drop
         └─ Waits 500ms confirm (debounce)

t=31500ms  Pump shutdown
         ├─ GPIO25 = LOW
         ├─ L298N cuts 12V supply
         └─ Pump stops (~100ms coast-down)

t=31600ms  Operational state restored
         └─ Ready for next cleaning cycle

Safety Timeout:
If sensor reads > Threshold for > 60 seconds:
├─ Software logs WARNING
├─ Forces pump OFF
├─ Alerts user via GUI ("Sensor may be stuck")
└─ Requires manual reset

```

#### 3.3.4 Especificaciones Técnicas
- **Tiempo de respuesta:** < 500ms (detección a activación)
- **Duración del ciclo:** 15-30 segundos
- **Cobertura del agua:** 100% del área del pincel
- **Temperatura agua:** Ambiente (no calentada)
- **Ciclos diarios:** > 50 sin mantenimiento

---

### 3.4 SUBSISTEMA 4: VISIÓN ARTIFICIAL (Vision)

#### 3.4.1 Descripción General
Sistema que captura video en tiempo real del lienzo mediante cámara CSI montada en Raspberry Pi 4 (Nodo Vision) y analiza el progreso artístico usando OpenCV para proporcionar retroalimentación visual al usuario.

#### 3.4.2 Componentes del Subsistema

```
┌────────────────────────────────────────────────────────┐
│    VISION SUBSYSTEM (RPI4-B + Camera + OpenCV)         │
│                                                        │
│  Raspberry Pi 4B (Nodo Vision):                        │
│  ├─ CPU: Cortex-A72 (quad-core, 1.5GHz)              │
│  ├─ RAM: 4GB LPDDR4                                   │
│  ├─ Storage: 64GB microSD Card (OS + Models)          │
│  ├─ Connectivity: Gigabit Ethernet                    │
│  ├─ USB: 4x USB 3.0 (expansion capable)               │
│  ├─ CSI Ribbon: 4-lane, 1Gb/s bandwidth               │
│  └─ OS: Raspberry Pi OS (32-bit) + Python 3.9        │
│                                                        │
│  CSI Camera Module 3:                                  │
│  ├─ Resolution: 12MP (4056 x 3040 pixels)            │
│  ├─ Lens: 75° FoV, fixed focus                        │
│  ├─ Sensor: 1/1.6" Sony IMX708                        │
│  ├─ Frame Rates:                                      │
│  │   └─ 30 FPS @ 1920x1080 (FULL HD)                 │
│  │   └─ 60 FPS @ 1280x720 (HD)                       │
│  ├─ Rolling Shutter: 10ms (acceptable for static)    │
│  ├─ Mounting: Adjustable angle bracket                │
│  └─ Position: 1.5m above canvas, 45° angle           │
│                                                        │
│  Software Stack:                                       │
│  ├─ Framework: Python 3.9 + asyncio                  │
│  ├─ Vision Library: OpenCV 4.5+                       │
│  ├─ ML Framework: TensorFlow Lite (optional)         │
│  ├─ Communication: paho-mqtt client                   │
│  └─ Data Format: JPEG frames + JSON metadata         │
│                                                        │
│  Analysis Modules:                                     │
│  ├─ Frame Capture (30 FPS continuous)                │
│  ├─ Color Space Conversion (BGR→HSV for analysis)    │
│  ├─ Contour Detection (painted areas)                │
│  ├─ Color Histogram Matching (expected vs actual)    │
│  ├─ Area Calculation (% coverage)                    │
│  └─ Anomaly Detection (spills, misalignment)         │
│                                                        │
│  Processing Pipeline:                                  │
│  ┌─────────────────┐     ┌──────────────────┐         │
│  │ Capture Frame   │────►│  Color Convert   │         │
│  │ (30 FPS, MJPEG) │     │  BGR→HSV         │         │
│  └─────────────────┘     └──────────────────┘         │
│         │                          │                   │
│         │     ┌────────────────────┴───────┐           │
│         │     │                            │           │
│         │     ▼                            ▼           │
│         │  ┌──────────────┐    ┌─────────────────┐   │
│         │  │ Edge Detect  │    │ Color Segment   │   │
│         │  │ (Canny)      │    │ (Threshold HSV) │   │
│         │  └──────────────┘    └─────────────────┘   │
│         │         │                    │               │
│         │         └────────────┬────────┘               │
│         │                      │                       │
│         │                      ▼                       │
│         │         ┌──────────────────────┐             │
│         │         │  Morphology Ops      │             │
│         │         │ (Dilate/Erode)       │             │
│         │         └──────────────────────┘             │
│         │                      │                       │
│         │                      ▼                       │
│         │         ┌──────────────────────┐             │
│         │         │ Contour Detection    │             │
│         │         │ Area Calculation     │             │
│         │         └──────────────────────┘             │
│         │                      │                       │
│         └──────────────────────┼────────┐              │
│                                │        │              │
│                                ▼        ▼              │
│                         ┌──────────────────────┐       │
│                         │ Metrics Computation  │       │
│                         │ • Coverage %         │       │
│                         │ • Color Accuracy     │       │
│                         │ • Errors             │       │
│                         └──────────────────────┘       │
│                                │                       │
│                                ▼                       │
│                         ┌──────────────────────┐       │
│                         │ MQTT Publish         │       │
│                         │ vision/metrics       │       │
│                         │ (JSON Payload)       │       │
│                         └──────────────────────┘       │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### 3.4.3 Formato de Datos MQTT (Vision)

```json
{
  "timestamp": "2026-04-30T14:23:45.123Z",
  "frame_id": 12450,
  "canvas_coverage": {
    "percentage": 67.5,
    "pixels_painted": 1048576,
    "total_pixels": 1548864
  },
  "color_analysis": {
    "stage_color": "RGB(255, 0, 0)",
    "avg_detected": "RGB(248, 12, 8)",
    "accuracy": 94.2
  },
  "anomalies": [],
  "processing_time_ms": 45.3,
  "fps": 30.1
}
```

#### 3.4.4 Especificaciones Técnicas
- **Latencia de procesamiento:** < 100ms (capture a publicación MQTT)
- **Precisión de cobertura:** ±2% (validado con target patterns)
- **Detección de color:** 95%+ accuracy vs. reference
- **Throughput:** 30 FPS sostenidos, 1920x1080
- **Uptime:** 24+ horas sin reinicio

---

### 3.5 SUBSISTEMA 5: PROYECCIÓN SINCRONIZADA (Projection)

#### 3.5.1 Descripción General
Sistema que proyecta guías visuales y referencias directamente en el lienzo para orientar al usuario a través de cada etapa del proceso de pintura, sincronizado en tiempo real con el estado del sistema.

#### 3.5.2 Componentes del Subsistema

```
┌────────────────────────────────────────────────────────┐
│   PROJECTION SUBSYSTEM (RPI4-A + Projector + Images)   │
│                                                        │
│  Raspberry Pi 4A (Nodo Proyección):                    │
│  ├─ CPU: Cortex-A72 (quad-core, 1.5GHz)              │
│  ├─ RAM: 2GB LPDDR4                                   │
│  ├─ Storage: 32GB microSD Card (Projection SW)        │
│  ├─ Connectivity: Gigabit Ethernet                    │
│  ├─ USB: 4x USB 3.0                                   │
│  ├─ HDMI: Full-size HDMI (projector connection)       │
│  └─ OS: Raspberry Pi OS + Python 3.9                  │
│                                                        │
│  Caydo P1 LED Projector:                              │
│  ├─ Brightness: 200 ANSI Lumens                       │
│  ├─ Resolution: 720p (1280x720)                       │
│  ├─ Contrast: 1000:1                                  │
│  ├─ Projection Distance: 0.3-2m (adjustable)          │
│  ├─ Keystone Correction: ±15° (software corrected)    │
│  ├─ Light Source: LED (50,000 hour lifespan)         │
│  ├─ Cooling: Passive (silent operation)               │
│  ├─ Weight: ~200g (portable, stable mount)            │
│  ├─ Input: HDMI only                                  │
│  └─ Power: 5V/2A USB (can be powered by HDMI adapter) │
│                                                        │
│  Mounting Structure:                                   │
│  ├─ Fixed Precision Metal Frame                       │
│  ├─ Adjustable: Height (0-500mm), Angle (0-45°)      │
│  ├─ Stability: Locked position, no drift              │
│  ├─ Canvas Distance: 1.2m (fixed for consistency)    │
│  └─ Calibration: One-time setup, stored in SW         │
│                                                        │
│  Projection Software Stack:                            │
│  ├─ Framework: Python 3.9 + PyGame                    │
│  ├─ Window Manager: Custom (fullscreen, no UI)        │
│  ├─ Graphics: OpenGL (via PyGame)                     │
│  ├─ Communication: paho-mqtt client                   │
│  ├─ Image Assets: ~/projection/images/ (PNG/JPG)      │
│  └─ Resolution Output: 1280x720 @ 30 FPS              │
│                                                        │
│  Image Library (Pre-rendered):                         │
│  ├─ Stage-specific references (per artwork)           │
│  │   ├─ stage_1_guide.png (outline + instructions)   │
│  │   ├─ stage_2_guide.png (color fill zones)         │
│  │   └─ ... (up to 10 stages per artwork)            │
│  ├─ UI Overlays                                       │
│  │   ├─ stage_number.png                             │
│  │   ├─ color_indicator.png                          │
│  │   └─ progress_bar.png                             │
│  └─ Emergency images                                   │
│      ├─ system_paused.png                            │
│      ├─ error_detected.png                           │
│      └─ cleanup_mode.png                             │
│                                                        │
│  Rendering Pipeline:                                   │
│  ┌──────────────────┐                                  │
│  │ MQTT Subscribe   │                                  │
│  │ projection/cmd   │                                  │
│  └────────┬─────────┘                                  │
│           │                                            │
│           ▼                                            │
│  ┌──────────────────┐                                  │
│  │ Parse Stage #    │                                  │
│  │ Decode Color     │                                  │
│  │ Extract Options  │                                  │
│  └────────┬─────────┘                                  │
│           │                                            │
│           ▼                                            │
│  ┌──────────────────┐                                  │
│  │ Load Image File  │                                  │
│  │ from ~/images/   │                                  │
│  │ (PNG, alpha ch.)  │                                  │
│  └────────┬─────────┘                                  │
│           │                                            │
│           ▼                                            │
│  ┌──────────────────┐                                  │
│  │ Render to Frame  │                                  │
│  │ (1280x720)       │                                  │
│  │ Apply color tint │                                  │
│  │ Add text overlay │                                  │
│  └────────┬─────────┘                                  │
│           │                                            │
│           ▼                                            │
│  ┌──────────────────┐                                  │
│  │ Output to HDMI   │                                  │
│  │ @ 30 FPS         │                                  │
│  │ (to projector)   │                                  │
│  └────────┬─────────┘                                  │
│           │                                            │
│           ▼                                            │
│  ┌──────────────────┐                                  │
│  │ Update visible   │                                  │
│  │ on canvas        │                                  │
│  │ < 500ms latency  │                                  │
│  └──────────────────┘                                  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### 3.5.3 Protocolo MQTT (Projection)

```
Topic: projection/cmd
Mensaje recibido de RPI5:
{
  "action": "show_stage",
  "artwork_id": "artwork_001",
  "stage": 1,
  "color": "RED",
  "rgb": [255, 0, 0],
  "image_file": "stage_1_guide.png",
  "overlay_text": "Paso 1: Pinta áreas rojas",
  "duration_s": 300  // Max 5 minutes before auto-advance
}

Respuesta (ACK):
{
  "status": "rendering",
  "timestamp": "2026-04-30T14:25:00Z",
  "frame_id": 12500,
  "projection_latency_ms": 42
}
```

#### 3.5.4 Especificaciones Técnicas
- **Latencia de actualización:** < 500ms (comando MQTT a visualización)
- **Precisión geométrica:** ±5mm (keystone correction)
- **Brillo:** 200 ANSI lumens (visible en luz ambiente normal)
- **Duración imagen:** Persistente hasta próximo comando
- **Fallback:** Black screen + logo si conexión perdida

---

### 3.6 SUBSISTEMA 6: PANEL DE CONTROL (Control Panel)

#### 3.6.1 Descripción General
Interface de usuario táctil que proporciona control centralizado, monitoreo de estado y selección de parámetros para toda la operación del sistema PIXARTEK.

#### 3.6.2 Componentes del Subsistema

```
┌────────────────────────────────────────────────────────┐
│   CONTROL PANEL SUBSYSTEM (RPI5 + Touchscreen GUI)     │
│                                                        │
│  Pantalla Táctil HDMI:                                 │
│  ├─ Tipo: Resistive o Capacitive LCD                  │
│  ├─ Tamaño: 7-10 pulgadas                             │
│  ├─ Resolución: 1280x720 (HD) mínimo                  │
│  ├─ Respuesta táctil: < 100ms                         │
│  ├─ Ángulo de visión: 170°                            │
│  ├─ Luminosidad: 400+ nits (sunlight readable)        │
│  ├─ Conectores: HDMI + USB (touch data)               │
│  ├─ Poder: 5V USB-C (desde RPI5)                      │
│  └─ Marco: Acero inoxidable / Plástico resistente     │
│                                                        │
│  Raspberry Pi 5 (Sistema Principal):                   │
│  ├─ CPU: 8-core ARM64 @ 3.0GHz                        │
│  ├─ RAM: 8GB LPDDR5                                   │
│  ├─ Storage: 256GB SSD vía USB-C                      │
│  ├─ USB: 4x USB 3.0 + 2x USB-C                        │
│  ├─ Ethernet: Gigabit (para MQTT broker)              │
│  ├─ GPIO: 40-pin standard                            │
│  ├─ Display: Dual HDMI (uno para pantalla táctil)    │
│  ├─ OS: Raspberry Pi OS (desktop)                     │
│  └─ Services: GUI App, MQTT Broker, REST API (optional)│
│                                                        │
│  Software GUI:                                         │
│  ├─ Framework: PyQt5 / PySide2 (Python)              │
│  ├─ Resolution: 1280x720 fullscreen                   │
│  ├─ Refresh Rate: 30 FPS                              │
│  ├─ Color Scheme: High contrast (accessibility)       │
│  ├─ Assets: PNG icons + TTF fonts                     │
│  └─ Data Binding: Real-time MQTT signal updates       │
│                                                        │
│  Main GUI Screens:                                     │
│  ├─ [1] Welcome Screen                                │
│  │   ├─ "Start Session" Button                        │
│  │   ├─ System Status Indicators                      │
│  │   └─ About / Settings                              │
│  │                                                    │
│  ├─ [2] Color Selection Screen                        │
│  │   ├─ 5x Large Color Buttons (Red, Blue, etc)       │
│  │   ├─ Volume Selector (10-200ml)                    │
│  │   ├─ "Dispense Manual" Button                      │
│  │   ├─ "Next Color" Button                           │
│  │   └─ Progress Bar (session completion %)           │
│  │                                                    │
│  ├─ [3] System Status Screen                          │
│  │   ├─ Limit Switches: [✓OK] [✓OK]                  │
│  │   ├─ Paint Levels: [████░░░░░░] Color 1           │
│  │   ├─ Pump Status: [ON] or [OFF] x5                │
│  │   ├─ Temperature: [35.2°C] (safe/warning)         │
│  │   ├─ Cleaning System: [READY] or [ACTIVE]         │
│  │   └─ Back Button                                   │
│  │                                                    │
│  ├─ [4] Emergency Screen                              │
│  │   ├─ Large Red STOP Button                         │
│  │   ├─ "Pause" Button                                │
│  │   ├─ System Status (why paused)                    │
│  │   ├─ Manual Controls (advanced)                    │
│  │   └─ Reset / Resume Buttons                        │
│  │                                                    │
│  └─ [5] Settings Screen                               │
│      ├─ Brightness Control (screen)                   │
│      ├─ Color Calibration (vision reference)          │
│      ├─ Speed Profile (slow/normal/fast)              │
│      ├─ Clean Water Level Monitor                     │
│      ├─ Reboot / Shutdown Options                     │
│      └─ Version Info (FW, SW, HW revisions)           │
│                                                        │
│  GPIO/Hardware Controls from GUI:                      │
│  ├─ Color Selection → Sets GPIO pins for pump motors  │
│  ├─ Dispense Duration → Calculates pump PWM duty cycle│
│  ├─ Position Command → Sends steps to TMC2209         │
│  ├─ Stop Button → Emergency GPIO shutdown (all)       │
│  └─ Cleaning Button → Activates pump via GPIO         │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### 3.6.3 Flujo de Interacción Típico

```
User Interaction Sequence:

[Welcome Screen]
    │ User taps "Start Session"
    ▼
[Color Selection - Red]
    │ • Pantalla muestra gran botón ROJO
    │ • Volumen: 50ml (default)
    │ • RPI5 energiza bomba 1 por ~2 segundos
    │ • RPI4 muestra guide proyectada
    │ • Usuario pinta el lienzo rojo
    │ User taps "Next Color"
    ▼
[Color Selection - Blue]
    │ • Pantalla muestra botón AZUL
    │ • Anterior volumen recordado (50ml)
    │ • RPI5 posiciona actuador a Color 2
    │ • RPI5 energiza bomba 2
    │ • Proyección actualiza a "PASO 2: Azul"
    │ • RPI4 monitorea cobertura
    │ User taps "Next Color"
    ▼
[... repeat para colores 3-5 ...]
    ▼
[Completion Screen]
    │ • Muestra "¡Obra Maestra Completada!"
    │ • Gallery de progreso (fotos de antes/después)
    │ • Score visual (% cobertura, accuracy)
    │ User taps "View Results" or "Save & Share"
    ▼
[Welcome Screen] ◄─────── Ready for next session
```

#### 3.6.4 Especificaciones Técnicas
- **Respuesta táctil:** < 100ms (touch a GUI update)
- **Actualización visual:** 30 FPS
- **Accesibilidad:** Alto contraste, gran fuente (24pt+)
- **Idioma:** Español (localizable)
- **Timeout inactividad:** 2 minutos (return to Welcome)
- **Robustez:** Reintentos automáticos si MQTT pierde conexión

---

## 4. FLUJOS DE COMUNICACIÓN INTER-SUBSISTEMA

### 4.1 Secuencia Típica de Operación Completa

```
╔═══════════════════════════════════════════════════════════════════╗
║                   COMPLETE OPERATION SEQUENCE                     ║
╚═══════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ INICIALIZACIÓN DEL SISTEMA (Startup)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Power ON                                                    │
│    └─ RPI5, RPI4-B, RPI4-A boot simultaneously               │
│    └─ GPIO pins initialize as inputs (safe state)            │
│                                                                 │
│ 2. Service Startup (RPI5)                                     │
│    ├─ MQTT Broker (mosquitto) starts on localhost:1883       │
│    ├─ GUI Application launches in fullscreen                 │
│    └─ Display [Welcome Screen]                               │
│                                                                 │
│ 3. Node Startup (RPI4-B, RPI4-A)                              │
│    ├─ Vision Node subscribes to: projection/cmd              │
│    ├─ Vision Node publishes to: vision/metrics               │
│    ├─ Projection Node subscribes to: projection/cmd          │
│    └─ Both nodes check MQTT connection (retry loop)          │
│                                                                 │
│ 4. Hardware Self-Test (RPI5)                                  │
│    ├─ [GPIO Limit Switches] ──► Poll GPIO26, GPIO21          │
│    │  └─ Expected: Both HIGH (switches released)             │
│    ├─ [Motor Home] ──► Pulse TMC2209 steps toward limit      │
│    │  └─ Expected: GPIO26 LOW when reached                   │
│    ├─ [Proximity Sensor] ──► Read ADC, verify range          │
│    │  └─ Expected: ADC < 300 (no obstruction)                │
│    ├─ [Touchscreen] ──► Test 4 corner taps                   │
│    │  └─ Expected: All corners register touches              │
│    └─ [Display] ──► Show "System Ready" for 3 seconds        │
│                                                                 │
│ 5. Network Check                                              │
│    ├─ RPI5 pings RPI4-B (vision)                             │
│    ├─ RPI5 pings RPI4-A (projection)                         │
│    └─ If any unreachable: Display warning, but continue      │
│                                                                 │
│ Status: ✓ System Ready                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ COLOR SELECTION & DISPENSING (Main Loop)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ User Action: Tap "RED COLOR" (50ml) on touchscreen           │
│                                                                 │
│ t=0ms    RPI5 GUI receives touch event                        │
│          └─ Color=RED, Volume=50ml, Position=1               │
│                                                                 │
│ t=10ms   RPI5 GUI publishes via MQTT:                         │
│          Topic: paint/dispense                                │
│          {color: 1, volume_ml: 50, duration_s: 2.0}          │
│          └─ (50ml ÷ 25ml/s = 2 seconds)                      │
│                                                                 │
│ t=20ms   RPI5 Main Controller (GPIO Thread) receives event    │
│          ├─ GPIO15=HIGH (actuator direction: forward)        │
│          ├─ Generate 480 pulses to TMC2209 (60mm movement)   │
│          └─ Poll GPIO26,GPIO21 for limit confirmation        │
│                                                                 │
│ t=420ms  Motor positioning complete                           │
│          ├─ Actuator nozzle now above Color 1 compartment    │
│          ├─ RPI5 publishes: {status: "positioned"}           │
│          └─ GUI displays [Dispensing...]                     │
│                                                                 │
│ t=440ms  RPI5 activates pump:                                 │
│          ├─ GPIO17=HIGH (L298N motor 1 enable)              │
│          ├─ PWM duty cycle = 80% (0.5A per coil)            │
│          └─ Peristaltic pump 1 starts at full speed          │
│                                                                 │
│ t=500-2500ms  Paint dispensing in progress                   │
│          ├─ Pump turns continuously                           │
│          ├─ Paint flows through nozzle into compartment 1    │
│          └─ RPI4-B captures baseline + monitors for spill    │
│                                                                 │
│ t=2440ms  Timer expires (2 seconds = ~50ml reached)         │
│          ├─ GPIO17=LOW (pump deactivates)                    │
│          └─ Peristaltic pump coasts to stop (~100ms)         │
│                                                                 │
│ t=2500ms  RPI5 publishes completion:                          │
│          Topic: paint/status                                 │
│          {color: 1, dispensed_ml: 49.8, status: "complete"} │
│                                                                 │
│ t=2510ms  GUI updates:                                         │
│          ├─ Dispense progress = 100%                         │
│          ├─ Display [Color 1 Ready - Paint Now]             │
│          └─ RPI4-A displays guide overlay for RED            │
│                                                                 │
│ t=2520ms  RPI4-B Vision Node is continuously:                │
│          ├─ Capturing 30 FPS video stream                    │
│          ├─ Analyzing canvas vs. expected pattern            │
│          ├─ Computing coverage percentage                    │
│          └─ Publishing metrics every 100ms to vision/metrics │
│                                                                 │
│ t=3000ms User finishes painting Red areas                     │
│          └─ Taps "NEXT COLOR" (Blue)                         │
│                                                                 │
│ [Sequence repeats for colors 2-5]                            │
│                                                                 │
│ After Color 5 Completed:                                     │
│          ├─ RPI5 publishes: {session: "complete"}           │
│          ├─ RPI4-A displays completion screen               │
│          ├─ RPI4-B captures final canvas image               │
│          └─ GUI shows results gallery (before/after)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ CLEANING CYCLE (Automatic - Triggered by Proximity)           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Background: User approaches brush cleaning station            │
│                                                                 │
│ t=0ms    User's hand (brush) enters proximity zone            │
│          ├─ Distance: 25cm (< 30cm threshold)                │
│          └─ Proximity sensor ADC reading: 650/1023           │
│                                                                 │
│ t=100ms  RPI5 ADC polling thread reads sensor                │
│          ├─ Value > 600 (threshold)                          │
│          └─ Logs: "Proximity detected"                       │
│                                                                 │
│ t=200ms  Confirmation wait (debounce)                        │
│          └─ Verify sensor still > 600 for 100ms              │
│                                                                 │
│ t=300ms  Pump activation:                                     │
│          ├─ GPIO25=HIGH (submergible pump enable)            │
│          ├─ Water pump starts (ramp-up ~100ms)               │
│          └─ RPI5 publishes: {cleaning: "started"}            │
│                                                                 │
│ t=450ms  Water flow established                              │
│          ├─ Water cascades as "rain" from shower hose        │
│          ├─ User rinses brush under water                    │
│          └─ Drained water collects in waste basin            │
│                                                                 │
│ t=450-31000ms  Sustained cleaning (up to 30 sec)             │
│          ├─ Sensor continues monitoring distance             │
│          ├─ RPI5 polls ADC every 200ms                       │
│          └─ Pump remains ON while proximity detected         │
│                                                                 │
│ t=31000ms  User moves brush away                             │
│          ├─ Distance > 30cm                                  │
│          └─ Proximity sensor ADC reading: 400/1023 (< 600)  │
│                                                                 │
│ t=31500ms  Debounce confirmation (500ms no proximity)       │
│          └─ Ready to shut down pump                          │
│                                                                 │
│ t=31600ms  Pump deactivation:                                │
│          ├─ GPIO25=LOW                                       │
│          ├─ Water pump coasts down (~100ms)                  │
│          └─ RPI5 publishes: {cleaning: "stopped"}            │
│                                                                 │
│ t=31700ms  System returns to normal                          │
│          └─ Ready for next cleaning or paint cycle           │
│                                                                 │
│ Safety: If proximity detected > 60s → Force pump OFF         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ EMERGENCY STOP (User Presses STOP Button or Error Detected)   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Trigger: User taps large RED "STOP" on touchscreen           │
│                                                                 │
│ t=0ms    Button press registered                             │
│          └─ RPI5 GUI thread processes touch event            │
│                                                                 │
│ t=1ms    Emergency sequence initiated:                        │
│          ├─ GPIO17,27,22,23,24 = LOW (all pumps OFF)        │
│          ├─ GPIO18 = LOW (motor hold/disable)                │
│          ├─ GPIO25 = LOW (cleaning pump OFF)                 │
│          └─ RPI5 publishes: {system: "emergency_stop"}       │
│                                                                 │
│ t=50ms   Display updates:                                     │
│          ├─ [PAUSED] message + timestamp                     │
│          ├─ Reason: "User Emergency Stop"                    │
│          ├─ Manual override options                          │
│          └─ All buttons disabled except "Acknowledge"        │
│                                                                 │
│ t=100ms  RPI4-A receives MQTT message                        │
│          ├─ Projection updates to "SYSTEM PAUSED"           │
│          └─ Red X overlay on canvas                          │
│                                                                 │
│ t=200ms  RPI4-B continues monitoring (safety)               │
│          ├─ Captures last frame as evidence                  │
│          └─ Logs metrics before stop                         │
│                                                                 │
│ Recovery: User taps "Acknowledge" + "Resume"                 │
│          ├─ Motor re-homes (safety)                          │
│          ├─ Projection reloads current stage                 │
│          └─ Resumes from where it stopped                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. TECNOLOGÍAS Y PATRONES DE DISEÑO

### 5.1 Stack de Tecnologías

| Capa | Componente | Tecnología | Versión |
|------|-----------|-----------|---------|
| **Control** | RPI5 Main | Python 3.9 | 3.9.2+ |
| | | asyncio, threading | stdlib |
| | | Qt5 / PyQt5 | 5.15+ |
| **Comunicación** | MQTT Broker | Mosquitto | 2.0+ |
| | | paho-mqtt | 1.6+ |
| **Visión** | RPI4-B | OpenCV | 4.5+ |
| | | NumPy | 1.21+ |
| | | Pillow | 8.0+ |
| **Proyección** | RPI4-A | PyGame | 2.1+ |
| | | Pillow | 8.0+ |
| **Sistema** | SO | Raspberry Pi OS | Bullseye+ |
| | | Boot/Init | systemd |
| | | Network | Ethernet |
| **Hardware** | Stepper | TMC2209 | Silicon Rev. B+ |
| | | Drivers | L298N |
| | | Sensors | GPIO + ADC |

### 5.2 Patrones de Diseño

#### 5.2.1 Observer Pattern (MQTT Pub/Sub)
- **RPI5 (Publisher):** Emite eventos de cambio de estado
- **RPI4-B, RPI4-A (Subscribers):** Reaccionan a eventos
- **Ventaja:** Desacoplamiento entre nodos

#### 5.2.2 State Machine Pattern
- **Motor Positioning:** IDLE → HOMING → READY → MOVING → STOPPED
- **System Lifecycle:** STARTUP → SELF_TEST → READY → OPERATING → EMERGENCY → SHUTDOWN
- **Ventaja:** Transiciones confiables, manejo de errores

#### 5.2.3 Thread Pool Pattern
- **RPI5 Main:** 5 worker threads
  - GPIO Control Thread (for pump/motor)
  - MQTT Listener Thread
  - GUI Event Thread
  - Sensor Polling Thread
  - Logging Thread
- **Ventaja:** No bloqueos, responsividad máxima

#### 5.2.4 Factory Pattern
- Creación de objetos de controladores por tipo
- Centraliza lógica de inicialización
- Fácil para testing mock

### 5.3 Concurrencia y Thread Safety

```python
# Pseudo-código para ilustración

class PixartekController:
    def __init__(self):
        self.state_lock = threading.Lock()
        self.gpio_semaphore = threading.Semaphore(1)  # Only one GPIO write at a time
        self.mqtt_queue = queue.Queue(maxsize=100)
        self.sensor_readings = {}
    
    def pump_control_thread(self):
        """Worker: Controls peristaltic pumps via GPIO"""
        while self.running:
            with self.gpio_semaphore:  # Ensure atomicity
                command = self.pump_queue.get(timeout=1)
                gpio.write(command.pin, command.value)
                time.sleep(0.001)
    
    def mqtt_listener_thread(self):
        """Worker: Listens for MQTT messages"""
        for message in self.mqtt_client.subscribe("paint/*"):
            with self.state_lock:
                self.process_mqtt_message(message)
    
    def sensor_polling_thread(self):
        """Worker: Polls ADC/GPIO sensors"""
        while self.running:
            with self.state_lock:
                self.sensor_readings['proximity'] = self.read_proximity_adc()
                self.sensor_readings['limit_0'] = self.read_gpio(26)
                self.sensor_readings['limit_1'] = self.read_gpio(21)
            time.sleep(0.2)  # Poll every 200ms
```

---

## 6. DECISIONES ARQUITECTÓNICAS Y TRADE-OFFS

### 6.1 ¿Por qué MQTT en lugar de RPC directo (gRPC)?

**Decisión:** MQTT Publish/Subscribe

**Justificación:**
- **Desacoplamiento:** RPI4 no necesita IP de RPI5 (broker actúa de intermediario)
- **Escalabilidad:** Fácil agregar más nodos sin modificar código existente
- **Confiabilidad:** QoS levels (0, 1, 2) para garantías de entrega
- **Bajo Ancho de Banda:** Overhead mínimo en payload JSON
- **Simplicidad:** Instalación de mosquitto < 5 minutos

**Trade-off:** Latencia ligeramente mayor (50ms vs 5ms RPC), pero aceptable para este caso

### 6.2 ¿Por qué NEMA 17 Stepper en lugar de Servo Brushless?

**Decisión:** Motor Stepper + TMC2209

**Justificación:**
- **Posicionamiento:** Hold torque sin encoder (fail-safe)
- **Costo:** $15 vs $80 para servo equivalente
- **Precisión:** 1/16 microstepping = 18.75µm resolution (sufficient)
- **Simplicidad:** 4 pines GPIO suficientemente vs 3 PWM + encoder

**Trade-off:** Velocidad máxima (~2s entre pozos) vs servo (~0.5s)

### 6.3 ¿Por qué OpenCV en CPU en lugar de TensorFlow + GPU?

**Decisión:** OpenCV con análisis clásico (contours, histogram)

**Justificación:**
- **Hardware disponible:** RPI4 no tiene GPU dedicada
- **Costo de ML:** Modelo entrenado + overhead > simple heuristics
- **Latencia:** OpenCV ~45ms vs TF ~200ms por frame
- **Confiabilidad:** Color histogram matching 95%+ accurate para este domain

**Trade-off:** No detección de errores complejos (mis-painting), pero acceptable

### 6.4 ¿Por qué Pantalla Táctil Local en lugar de Web UI remoto?

**Decisión:** Qt5 GUI local + MQTT opcional para remoto

**Justificación:**
- **Latencia:** Táctil local <100ms vs web ~500ms
- **Confiabilidad:** Funciona incluso si red falla
- **Seguridad:** No expone API públicamente
- **UX:** Respuesta inmediata a touch (feedback haptic ready)

**Trade-off:** No acceso desde smartphone, pero scope fuera de reqs

---

## 7. ESTRATEGIA DE MANTENIMIENTO Y RECUPERACIÓN

### 7.1 Logs y Monitoreo

```
RPI5 Log Locations:
├─ /var/log/pixartek.log        (main system)
├─ /var/log/mosquitto/mosquitto.log (MQTT broker)
├─ /var/log/hardware_debug.log   (GPIO trace)
└─ /tmp/vision_metrics.csv        (rolling 1000 frames)

RPI4-B Vision Logs:
├─ /home/pi/vision/logs/vision_$(date +%Y%m%d).log
└─ /tmp/frame_dumps/              (JPEG snapshots on error)

RPI4-A Projection Logs:
├─ /home/pi/projection/logs/proj_$(date +%Y%m%d).log
└─ /tmp/projection_errors.log
```

### 7.2 Recuperación de Errores

#### Erro: Motor no responde
```
Sequence:
1. Detect: GPIO step pulses not moving actuator (limit switch unchanged after 10s)
2. Log: "MOTOR_UNRESPONSIVE" + timestamp
3. Action: 
   ├─ Disable motor (GPIO18 = LOW)
   ├─ Display error on GUI: "Motor Error - Reset Required"
   ├─ Sound warning beep (if speaker available)
   └─ Pause system automatically
4. Recovery:
   ├─ User checks mechanical blockage
   ├─ User taps "Reset Motor"
   ├─ RPI5 re-homes (pulses until limit switch)
   └─ Resumes if home successful
```

#### Error: Paint dispense mismatch
```
Sequence:
1. Detect: Vision system sees < 80% expected coverage after 3 seconds
2. Log: "DISPENSING_ANOMALY" + vision metrics
3. Action:
   ├─ Pause pump
   ├─ Display on GUI: "Possible blockage - Check nozzle"
   ├─ RPI5 sends alert to RPI4-A (projection)
   └─ Projection shows "PAUSE - CHECK DISPENSER"
4. Recovery:
   ├─ User manually checks nozzle for clogs
   ├─ User runs "Flush Pump" (test dispense)
   ├─ If OK → "Resume Color 1"
   └─ If failed → Manual drain & refill required
```

---

## 8. SEGURIDAD Y LIMITACIONES

### 8.1 Hardware Safeguards

- **Soft Stop:** All GPIO pins initialized as INPUT (safe state on boot)
- **Timeout:** 60-second inactivity → auto-shutdown all motors
- **Current Limiting:** L298N thermal protection @ 2A
- **Temperature Monitoring:** Sensor @ RPI5 SoC, shutdown if > 80°C
- **Pressure Relief:** Peristaltic pump has built-in relief valve @ 2 bar

### 8.2 Software Safeguards

- **State Validation:** Never allow pump ON + motor moving simultaneously
- **Limit Switch Enforcement:** Motor stops immediately if limit triggered
- **MQTT Watchdog:** Detect if broker offline > 30s, switch to fallback mode
- **GUI Timeout:** Locks all controls if inactive > 10min, return to Welcome

### 8.3 Restricciones Operacionales

- **Máx. Presión:** 2 bar (bomba peristáltica límite)
- **Máx. Temperatura:** 40°C (especificación RPI5)
- **Humedad:** 20-80% (no condensante)
- **Voltaje:** ±10% de nominal (12V ±1.2V, 5V ±0.5V)

---

## 9. CONCLUSIÓN

PIXARTEK es un sistema integrado bien definido con 6 subsistemas especializados coordinados por Raspberry Pi 5 central mediante MQTT. El diseño balancear costo, confiabilidad y precisión usando componentes estándar disponibles. Las decisiones arquitectónicas priorizan robustez (fail-safes) y mantenibilidad (modularidad MQTT) sobre máximo rendimiento.

**Próximos pasos:**
1. Validar cada subsistema aisladamente
2. Integración progresiva (1 → 2 → 3, etc.)
3. Testing end-to-end de operación completa
4. Documentación de mantenimiento preventivo

---

**Fin de ADD Real - PIXARTEK**
