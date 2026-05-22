# PIXARTEK - Architectural Design Document (ADD)
**Versión:** 1.0  
**Fecha:** Abril 2026  
**Estado:** Completo

---

## 1. INTRODUCCIÓN

### 1.1 Propósito
Este documento describe las decisiones de diseño arquitectónico de PIXARTEK, justificando las tecnologías seleccionadas, patrones de diseño, estructura de componentes, y trade-offs considerados.

### 1.2 Audiencia
- Desarrolladores del proyecto
- Arquitectos de sistemas
- Personal de operaciones y deployment
- Revisores de código

### 1.3 Alcance
Cubre arquitectura a nivel de:
- Distribución de componentes entre nodos
- Selección de tecnologías
- Protocolos de comunicación
- Patrones de diseño
- Decisiones de trade-off

---

## 2. DECISIONES ARQUITECTÓNICAS PRINCIPALES

### 2.1 Arquitectura Distribuida Multi-Nodo

#### Decisión
Implementar sistema en **3 nodos Raspberry Pi independientes** en lugar de single-machine

#### Razones
1. **Especialización**: Cada nodo realiza tarea específica
   - RPI5: Orquestación, interfaz, control
   - RPI4-B: Procesamiento intensivo (visión)
   - RPI4-A: Control de hardware (proyector)

2. **Escalabilidad**: Fácil agregar más nodos de visión
   - Múltiples cámaras sin saturar RPI5
   - Procesos de IA no bloquean UI

3. **Resiliencia**: Fallos aislados
   - Si Vision Node falla, Backend/Frontend continúan
   - Projector independiente de análisis

#### Alternativas Consideradas
| Opción | Pros | Contras | Decisión |
|--------|------|---------|----------|
| Single RPI5 | Simple, bajo costo | Bottleneck CPU/GPU | ❌ Rechazado |
| Multi-RPI (actual) | Especializado, escalable | Complejidad comunicación | ✅ **Seleccionado** |
| Cloud + Edge | Infinita escalabilidad | Latencia, costo | ❌ No aplica |

#### Implicaciones
- Requiere middleware (MQTT) para comunicación
- Sincronización eventual entre nodos
- Mayor complejidad operacional
- Mejor desempeño general

---

### 2.2 MQTT como Backbone de Comunicación

#### Decisión
Usar **MQTT Broker (Mosquitto)** como sistema de mensajería central

#### Razones
1. **Pub/Sub Desacoplado**: 
   - Productores y consumidores no necesitan conocerse
   - Vision Node y Projection Node operan independientemente

2. **Bajo Overhead**:
   - Diseñado para IoT/embebidos
   - ~80KB de RAM vs Redis (~100MB)

3. **Confiable**:
   - Garantías QoS (at-least-once, exactly-once)
   - Retenção de mensajes

4. **Flexible**:
   - Topics jerárquicos: `pixartek/vision/feedback`
   - Fácil agregar nuevos consumidores

#### Alternativas Consideradas
| Opción | Latencia | Overhead | Escalabilidad | Decisión |
|--------|----------|----------|---------------|----------|
| RabbitMQ | ~10ms | Alto (Java) | Excelente | ❌ Overkill |
| Redis | ~5ms | Medio | Muy buena | ❌ No es message broker |
| HTTP Polling | ~100ms+ | Alto | Pobre | ❌ Muy lento |
| MQTT (actual) | ~20ms | Bajo | Buena | ✅ **Seleccionado** |
| gRPC | ~5ms | Medio | Excelente | ❌ Complejidad |

#### Implicaciones
- Instalación de Mosquitto en RPI5
- Configuración de topics y QoS
- Debugging requiere mqtt-spy o similar
- Single point of failure (MQTT broker)

---

### 2.3 REST API vs WebSocket

#### Decisión
Usar **REST para comandos**, **WebSocket para feedback en tiempo real**

#### Razones

**REST para Commands:**
- Idempotente (seguro retry)
- Caching posible
- Simpler error handling
- Mejores prácticas HTTP

**WebSocket para Feedback:**
- Baja latencia (<100ms)
- Permite broadcast eficiente a múltiples clientes
- Evita polling (ahorra recursos)
- Mejor experiencia de usuario

#### Flujo de Comunicación
```
User Click → Frontend HTTP POST → Backend (create session)
                                  ↓
                           MQTT Publish (projection/command)
                                  ↓
Backend receives MQTT → WebSocket Broadcast to all clients
                                  ↓
Frontend receives via WebSocket → Update UI (feedback overlay)
```

#### Alternativas Consideradas
| Opción | Latencia | Escalabilidad | Complejidad |
|--------|----------|---------------|------------|
| Todo HTTP Polling | 1-5 segundos | Pobre | Baja |
| Todo WebSocket | <100ms | Buena | Media |
| REST + WS (actual) | Variable | Buena | Media | ✅

#### Implicaciones
- Doble capa de comunicación a mantener
- WebSocket requiere servidor que lo soporte (FastAPI sí)
- Cliente debe manejar reconexión automática

---

### 2.4 SQLite como Base de Datos

#### Decisión
Usar **SQLite** en lugar de PostgreSQL/MySQL

#### Razones
1. **Embebida**: Sin servidor separado requerido
2. **Bajo Overhead**: 1 archivo, 0 configuración
3. **Suficiente**: <1GB datos estimados
4. **Fácil Backup**: Un archivo a copiar

#### Alternativas Consideradas
| Opción | Setup | Performance | Escalabilidad |
|--------|-------|-------------|---------------|
| SQLite | 🟢 0 | 🟢 Bueno | 🟡 Limitado |
| PostgreSQL | 🔴 Complejo | 🟢 Excelente | 🟢 Infinito |
| MySQL | 🔴 Complejo | 🟢 Excelente | 🟢 Infinito |
| MongoDB | 🟡 Medio | 🟡 Medio | 🟢 Infinito |

**Seleccionado**: SQLite ✅ (tradeoff simplicity vs scale)

#### Limitaciones
- Concurrencia limitada (un writer)
- No apto para >100 sesiones simultáneas (actual: OK)
- No replicación nativa

#### Mitigaciones
- Índices en artwork_id, session_id
- Async queries con SQLAlchemy
- Backups automáticos

---

### 2.5 Next.js para Frontend

#### Decisión
Usar **Next.js 14** con TypeScript

#### Razones
1. **SSR + Static Generation**: Rápido, SEO
2. **File-based Routing**: Menos código boilerplate
3. **TypeScript Built-in**: Type safety
4. **Vercel Optimization**: Image optimization, API routes
5. **React 18**: Concurrent features, Suspense

#### Alternativas Consideradas
| Framework | Learning Curve | Performance | Bundle |
|-----------|----------------|-------------|--------|
| Vanilla React | Bajo | Bueno | Mediano |
| Vue.js | Muy bajo | Bueno | Pequeño |
| Svelte | Bajo | Excelente | Pequeño |
| Next.js | Medio | Excelente | Mediano |
| Nuxt | Medio | Excelente | Mediano |

**Seleccionado**: Next.js ✅

#### Justificación
- Proyecto requiere imagen optimization
- Rutas complejas (/catalog, /session, /settings, /welcome)
- TypeScript obligatorio para mantenibilidad

---

### 2.6 FastAPI para Backend

#### Decisión
Usar **FastAPI** sobre Django/Flask

#### Razones
1. **Async-First**: Diseñado para I/O async
   - MQTT no-blocking
   - WebSocket no-blocking
   - Database queries async

2. **Auto-Docs**: Swagger/OpenAPI automático
3. **Type Hints**: Pydantic validation
4. **Performance**: 2-3x más rápido que Flask
5. **Moderno**: Soporta Python 3.7+

#### Alternativas Consideradas
```
Flask: Rápido de aprender, pero síncrono
Django: Pesado, overkill para microservice
Bottle: Minimalista, sin async
FastAPI: ✅ Async, modern, performance
```

#### Patrones Implementados

**1. Dependency Injection**
```python
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/api/artworks")
async def get_artworks(db: AsyncSession = Depends(get_db)):
    ...
```

**2. Router Modularization**
```
app.include_router(artworks.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(hardware.router, prefix="/api")
```

**3. Lifespan Context**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    start_mqtt()
    yield
    # Shutdown
    stop_mqtt()
```

---

### 2.7 OpenCV para Análisis de Visión

#### Decisión
Usar **OpenCV** para procesamiento de imágenes

#### Razones
1. **Madurez**: 20+ años de desarrollo
2. **Performance**: Optimizado en C++, bindings Python
3. **Feature-Complete**: Contour detection, color space conversion, etc.
4. **Community**: Amplio soporte y ejemplos

#### Alternativas Consideradas
| Biblioteca | Performance | Ease | Features |
|-----------|-------------|------|----------|
| PIL/Pillow | Lento | Fácil | Básicas |
| scikit-image | Lento | Fácil | Buenas |
| OpenCV | Rápido | Medio | Excelentes |
| TensorFlow | Muy rápido | Difícil | Para ML |

**Seleccionado**: OpenCV ✅

#### Técnicas Implementadas
1. **Calibración**: Perspectiva + color
2. **Comparación de Imágenes**: Template matching + SSIM
3. **Detección de Errores**: Contours + area analysis
4. **Colorimetría**: Conversión a Lab para Delta-E

---

### 2.8 TypeScript para Frontend y Backend

#### Decisión
Usar **TypeScript** en lugar de JavaScript puro

#### Razones
1. **Type Safety**: Errores en compile-time, no runtime
2. **Mejor IDE Support**: Autocomplete, refactoring
3. **Self-Documenting**: Types sirven como documentación
4. **Reducir Bugs**: Especialmente en equipo

#### Tradeoff
- Tiempo de compilación (mitigado con esbuild/swc)
- Curva aprendizaje (vale la pena)

---

## 3. PATRONES DE DISEÑO

### 3.1 Patrón MVC (Model-View-Controller)

#### Backend
```
Models (SQLAlchemy):
├─ Artwork
├─ Session
├─ SessionMetric
└─ ArtworkStage

Routes (FastAPI):
├─ /api/artworks
├─ /api/sessions
├─ /api/hardware
└─ /api/vision

Business Logic:
├─ Session creation
├─ Stage progression
├─ Metric recording
└─ Hardware control
```

#### Frontend
```
Pages (Next.js):
├─ /catalog
├─ /session
├─ /settings
└─ /welcome

Components (React):
├─ FeedbackOverlay
├─ CameraLiveFeed
├─ HardwareControls
├─ SessionStore (Zustand)
└─ Hooks (useSession, useWebSocket)
```

### 3.2 Patrón Observer (Pub/Sub)

#### Implementación: MQTT
```
Producers:
└─ Vision Node → publishes pixartek/vision/feedback

Broker:
└─ Mosquitto → routes messages

Consumers:
├─ Backend → recibe y retransmite via WebSocket
└─ Projection Node → recibe commands
```

### 3.3 Patrón Repository

#### Backend Database Access
```python
class ArtworkRepository:
    async def get_all() -> List[Artwork]
    async def get_by_id(id: str) -> Artwork
    async def create(data: ArtworkCreate) -> Artwork

class SessionRepository:
    async def create(session: SessionCreate) -> Session
    async def update_stage(session_id, new_stage) -> Session
    async def record_metric(metric: MetricCreate) -> Metric
```

### 3.4 Patrón Service Locator / Dependency Injection

#### FastAPI
```python
# Dependencies
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Routes usan dependency
@app.post("/api/sessions")
async def create_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    ...
```

#### Frontend (Zustand Stores)
```typescript
// Global state management
const useSessionStore = create((set) => ({
  currentStage: 1,
  setStage: (stage) => set({ currentStage: stage }),
  ...
}))

// Components usan store
function SessionPage() {
  const { currentStage } = useSessionStore()
  ...
}
```

### 3.5 Patrón Adapter

#### Vision Node Message Adapter
```python
# MQTT message (raw)
mqtt_payload = {
    "precision_pct": 85.5,
    "color_deviation": 12.3,
    ...
}

# Adapter
def adapt_vision_feedback(mqtt_payload) -> VisionFeedbackDTO:
    return VisionFeedbackDTO(
        precision=mqtt_payload["precision_pct"],
        colors=mqtt_payload["color_deviation"],
        ...
    )
```

---

## 4. ESTRUCTURA DE DIRECTORIOS

```
pixartek/
├─ backend/
│  ├─ main.py                          # Entry point
│  ├─ requirements.txt                 # Dependencies
│  ├─ pixartek.db                      # SQLite database
│  │
│  └─ app/
│     ├─ core/
│     │  └─ config.py                  # Settings, environment
│     │
│     ├─ models/
│     │  ├─ artwork.py                 # Artwork model
│     │  ├─ session.py                 # Session model
│     │  ├─ artwork_stage.py           # Stage model
│     │  └─ __init__.py
│     │
│     ├─ db/
│     │  ├─ base.py                    # Database setup
│     │  ├─ seed.py                    # Initial data
│     │  └─ __init__.py
│     │
│     ├─ mqtt/
│     │  └─ client.py                  # MQTT publisher
│     │
│     ├─ api/
│     │  ├─ routes/
│     │  │  ├─ artworks.py             # GET /api/artworks
│     │  │  ├─ sessions.py             # CRUD /api/sessions
│     │  │  ├─ hardware.py             # Control GPIO
│     │  │  ├─ stages.py               # GET /api/stages
│     │  │  ├─ vision.py               # Vision endpoints
│     │  │  ├─ config.py               # Config endpoints
│     │  │  ├─ ws.py                   # WebSocket endpoint
│     │  │  └─ __init__.py
│     │  │
│     │  └─ __init__.py
│     │
│     └─ __init__.py
│
├─ frontend/
│  ├─ package.json                     # Dependencies
│  ├─ next.config.js                   # Next.js config
│  ├─ tailwind.config.ts               # Tailwind CSS
│  ├─ tsconfig.json                    # TypeScript config
│  │
│  └─ src/
│     ├─ app/
│     │  ├─ layout.tsx                 # Root layout
│     │  ├─ page.tsx                   # Home page
│     │  ├─ catalog/
│     │  │  └─ page.tsx                # Artwork listing
│     │  ├─ session/
│     │  │  └─ page.tsx                # Painting screen
│     │  ├─ settings/
│     │  │  └─ page.tsx                # Settings page
│     │  └─ welcome/
│     │     └─ page.tsx                # Intro page
│     │
│     ├─ components/
│     │  ├─ ui/
│     │  │  ├─ PixartekLogo.tsx        # Logo component
│     │  │  ├─ ArtworkCard.tsx         # Artwork card
│     │  │  ├─ CameraLiveFeed.tsx      # Camera preview
│     │  │  └─ VisionAnalysisModal.tsx # Modal display
│     │  │
│     │  ├─ kiosk/
│     │  │  ├─ HardwareControls.tsx    # Pigment control
│     │  │  ├─ FeedbackPanel.tsx       # Metrics display
│     │  │  ├─ NodeStatus.tsx          # System health
│     │  │  ├─ ProfilePicker.tsx       # User selection
│     │  │  └─ CompletionScreen.tsx    # Results screen
│     │  │
│     │  └─ feedback/
│     │     └─ FeedbackOverlay.tsx     # Real-time feedback
│     │
│     ├─ lib/
│     │  ├─ api-client.ts              # API calls
│     │  ├─ session-store.ts           # Zustand session state
│     │  ├─ profile-store.ts           # User state
│     │  └─ mock-artworks.ts           # Test data
│     │
│     ├─ hooks/
│     │  ├─ useSession.ts              # Session hook
│     │  ├─ useArtworks.ts             # Artworks hook
│     │  ├─ useWebSocket.ts            # WS connection
│     │  └─ useProfile.ts              # User hook
│     │
│     ├─ types/
│     │  ├─ artwork.ts                 # Type definitions
│     │  ├─ session.ts                 # Session types
│     │  └─ feedback.ts                # Feedback types
│     │
│     └─ public/
│        └─ (static assets)
│
├─ nodes/
│  ├─ vision/
│  │  ├─ main.py                       # Vision node entry
│  │  ├─ camera.py                     # Camera interface
│  │  ├─ analyzer.py                   # Image analysis
│  │  ├─ mqtt_client.py                # MQTT communication
│  │  └─ requirements.txt
│  │
│  └─ projection/
│     ├─ main.py                       # Projection node
│     ├─ projector.py                  # Projector control
│     ├─ mqtt_client.py                # MQTT listener
│     └─ requirements.txt
│
├─ shared/
│  └─ schemas/
│     └─ (JSON schemas, type defs)
│
├─ assets/
│  └─ artworks/
│     ├─ FARO-NOCTURNO-DIVISIONES/
│     ├─ FLORES-BLANCAS-DIVISIONES/
│     ├─ MUJER-EN-UN-SOMBRERO-DIVISIONES/
│     └─ TUCAN-TROPICAL-DIVISIONES/
│
├─ deploy/
│  └─ (deployment scripts)
│
├─ docker-compose.yml                  # Local dev setup
├─ ARCHITECTURE_BLOCK_DIAGRAM.md        # System architecture
├─ SYSTEM_REQUIREMENTS_SPECIFICATION.md # Requirements
└─ ARCHITECTURAL_DESIGN_DOCUMENT.md     # This file
```

---

## 5. FLUJOS DE INTEGRACIÓN CRÍTICOS

### 5.1 Flujo: Crear Sesión

```
┌─────────┐
│ Frontend│ POST /api/sessions
│ Click   │ {artwork_id, start_stage, total_stages}
│ "Start" │
└────┬────┘
     │
     ▼
┌──────────────────────────────┐
│ Backend                      │
│ 1. Validate artwork exists   │
│ 2. Create Session record     │
│ 3. Save to SQLite            │
│ 4. Return session_id         │
└────┬─────────────────────────┘
     │
     ▼
┌──────────────────────────────┐
│ Response to Frontend         │
│ {                            │
│   "session_id": "abc123",    │
│   "artwork_id": "xyz",       │
│   "current_stage": 1,        │
│   "total_stages": 4          │
│ }                            │
└────┬─────────────────────────┘
     │
     ▼
┌──────────────────────────────┐
│ Backend publishes MQTT       │
│ Topic: pixartek/projection/  │
│         command              │
│ Payload: {                   │
│   artwork_id,                │
│   stage: 1,                  │
│   image_path: "/artworks.." │
│ }                            │
└────┬─────────────────────────┘
     │
     ├─────────────────┬──────────────────┐
     │                 │                  │
     ▼                 ▼                  ▼
┌──────────┐    ┌───────────────┐  ┌────────────┐
│ Vision   │    │ Projection    │  │ Frontend   │
│ Node     │    │ Node          │  │ WebSocket  │
│ (sub)    │    │ (sub)         │  │ (via WS)   │
│          │    │               │  │            │
│ Load     │    │ Display       │  │ Ready for  │
│ ref img  │    │ reference     │  │ feedback   │
│          │    │ on projector  │  │            │
└──────────┘    └───────────────┘  └────────────┘
```

### 5.2 Flujo: Análisis Continuo

```
Vision Node (every ~2 sec):
  1. capture_frame()
  2. compare_to_reference(frame, ref_image)
  3. calculate_metrics()
     - precision_pct
     - color_deviation
     - stroke_errors
     - suggestions
  4. publish_mqtt("pixartek/vision/feedback", metrics)
       ↓
    MQTT Broker
       ↓
    Backend (subscribes to pixartek/vision/#)
       ↓
    Backend MQTT callback
       ↓
    Broadcast via WebSocket to all connected clients
       ↓
    Frontend receives via WebSocket
       ↓
    Update UI:
    - FeedbackOverlay (4 sec auto-close)
    - FeedbackPanel (metrics display)
    - Session store (persist metrics)
```

### 5.3 Flujo: Error Handling

```
Network Disconnected:
  Frontend
    ├─ Detect WebSocket close
    ├─ Show "Desconectado" indicator
    ├─ Attemp reconnect (exponential backoff)
    └─ If reconnected: re-sync state

MQTT Broker Down:
  Backend
    ├─ Detect MQTT disconnect
    ├─ Log error
    ├─ Attempt reconnect (exponential backoff)
    └─ Continue serving REST API (degraded mode)

Vision Node Crash:
  Frontend
    ├─ Stop receiving feedback messages
    ├─ After 5 sec timeout → show alert
    ├─ User can continue painting (manual mode)
    └─ Metrics saved but without vision data

Database Error:
  Backend
    ├─ Catch SQLAlchemy exception
    ├─ Return HTTP 500
    ├─ Log to console/file
    └─ Client should retry
```

---

## 6. DECISIONES DE TRADE-OFF

### 6.1 Sincronización Eventual vs Fuerte

**Decisión**: Usar sincronización eventual

**Tradeoff**:
```
Ventajas:
  ✅ Escalabilidad
  ✅ Tolerancia a fallos
  ✅ Bajo acoplamiento

Desventajas:
  ❌ Consistencia eventual (data lag)
  ❌ Complejidad en debugging
  ❌ Possible race conditions

Mitigación:
  - Mensajes de MQTT tienen timestamp
  - Frontend valida orden de mensajes
  - Backend ignora feedback antiguo
```

### 6.2 Caching vs Freshness

**Decisión**: Minimal caching, máxima freshness

**Razones**:
- Datos cambian frecuentemente (feedback cada 2 sec)
- Caching añadiría complejidad
- Ancho de banda es suficiente

**Lugares donde SFifth hay cache**:
- Browser cache (images, static assets)
- Artwork metadata (rara vez cambia)

### 6.3 Monolithic vs Microservices

**Decisión**: Monolithic con separación lógica

**Justificación**:
- Equipo pequeño (1-2 devs)
- Datos altamente acoplados
- Deployment simplificado
- Modularidad a través de separación de archivos

**Futura Consideración**:
Si Sistema crece, podría separarse en:
- `artworks-service`
- `sessions-service`
- `vision-service`
- `hardware-service`

### 6.4 Rendimiento vs Legibilidad de Código

**Decisión**: Priorizar legibilidad y mantenibilidad

**Ejemplo**:
```python
# Legible (actual)
precision_match = sum(1 for a, b in zip(pixels_actual, pixels_ref) if a == b)
precision_pct = (precision_match / len(pixels_ref)) * 100

# Performante pero menos claro
precision_pct = np.mean((np.array(pixels_actual) == np.array(pixels_ref)).astype(int)) * 100
```

---

## 7. COMPONENTES CRÍTICOS Y PUNTOS DE FALLA

### 7.1 MQTT Broker

**Criticidad**: 🔴 CRÍTICA

**Impacto de Falla**:
- Inter-nodo communication cesa
- Vision feedback no llega
- Projector no recibe comandos

**Mitigación**:
- Monitoring continuo (health checks)
- Auto-restart con systemd
- Backups de configuración

### 7.2 Database (SQLite)

**Criticidad**: 🔴 CRÍTICA

**Impacto de Falla**:
- Sessions no se guardan
- Metrics perdidas
- Artworks no accesibles

**Mitigación**:
- Backups diarios
- Transacciones ACID
- Checks de integridad

### 7.3 Vision Node

**Criticidad**: 🟡 IMPORTANTE

**Impacto de Falla**:
- Sin feedback visual
- Sistema sigue funcionando (modo manual)

**Mitigación**:
- Graceful degradation
- Frontend muestra "Vision unavailable"
- User puede continuar sin feedback

### 7.4 Projector / Camera Hardware

**Criticidad**: 🟡 IMPORTANTE

**Impacto de Falla**:
- No muestra referencia / no captura frames
- Experiencia degradada

**Mitigación**:
- Health checks periódicos
- Fallback UI (mostrar instrucciones en pantalla)

---

## 8. SEGURIDAD Y PRIVACIDAD

### 8.1 Comunicación

**MQTT**:
- Sin credenciales (red privada)
- Sin encriptación (local network)

**WebSocket**:
- Mismo origen que página HTTP
- CORS configurado

**REST API**:
- No requiere auth (sistema público)
- CORS enabled

### 8.2 Datos Sensibles

**Almacenados**:
- Nombre de usuario (opcional)
- Métricas de sesión (no-PII)
- Timestamps

**No Almacenados**:
- Imágenes de usuarios
- Datos biométricos
- Información de pago

### 8.3 GPIO Control

**Protección**:
- Solo Backend puede escribir GPIO
- Timeouts automáticos
- Validación de rangos

---

## 9. DEPLOYMENT Y OPERACIONES

### 9.1 Deployment Architecture

```
Development:
  └─ Single RPI5 con todos los servicios

Production:
  ├─ RPI5: Backend, Frontend, MQTT Broker
  ├─ RPI4-B: Vision Node
  └─ RPI4-A: Projection Node
```

### 9.2 Servcios Systemd

```
rpi5:
  ├─ pixartek-backend.service
  ├─ pixartek-frontend.service
  └─ mosquitto.service

rpi4-b:
  └─ pixartek-vision.service

rpi4-a:
  └─ pixartek-projection.service
```

### 9.3 Health Checks

```
Backend:
  GET /health → {status: "ok", node: "rpi5-main"}

MQTT:
  PING/PONG protocol (built-in)

Frontend:
  Browser dev tools (connection status)

Vision:
  Publish heartbeat every 5 sec
```

---

## 10. ROADMAP Y FUTURO

### Fase 1 (Actual): MVP
- ✅ 4 obras base
- ✅ 3-5 etapas por obra
- ✅ Feedback visual en tiempo real
- ✅ Control de dispensador

### Fase 2 (Próximo Trimestre)
- [ ] Dashboard de métricas
- [ ] Profiles de usuario con histórico
- [ ] Soporte para múltiples idiomas
- [ ] Mobile app (Expo/React Native)

### Fase 3 (Q3 2026)
- [ ] Machine learning para mejor detección
- [ ] Integración con proyector 3D
- [ ] Colaboración en vivo (múltiples usuarios)
- [ ] API pública para extensiones

### Fase 4 (Q4 2026+)
- [ ] Escalado a múltiples nodos de visión
- [ ] Cloud sync (backup remoto)
- [ ] Gamification (puntos, logros)
- [ ] Análisis de datos y reportes

---

## 11. REFERENCIA DE TECNOLOGÍAS

| Tecnología | Versión | Propósito | Rationale |
|-----------|---------|----------|-----------|
| Python | 3.11+ | Backend, Vision | Comunidad científica, sintaxis simple |
| Node.js | 18+ | Frontend | Ecosistema npm, desarrollo rápido |
| FastAPI | 0.104+ | Web Framework | Async, performance, auto-docs |
| Next.js | 14+ | Frontend Framework | SSR, file routing, optimización |
| SQLite | 3.40+ | Database | Embebida, zero-config |
| Mosquitto | 2.0+ | MQTT Broker | Lightweight, reliable |
| SQLAlchemy | 2.0+ | ORM | Type hints, migrations |
| Pydantic | 2.0+ | Validation | Type safety, auto-docs |
| React | 18+ | UI Library | Component-based, virtual DOM |
| TypeScript | 5.0+ | Language | Type safety, IDE support |
| Tailwind CSS | 3.0+ | Styling | Utility-first, responsive |
| Zustand | Latest | State Management | Minimal, hook-based |
| OpenCV | 4.8+ | Image Processing | Performance, features |
| Picamera2 | Latest | Camera Capture | Official Raspberry Pi library |

---

**Fin del Documento de Diseño Arquitectónico**
