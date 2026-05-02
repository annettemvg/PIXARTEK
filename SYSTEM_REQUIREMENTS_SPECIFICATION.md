# PIXARTEK - System Requirements Specification (SRS)
**Versión:** 1.0  
**Fecha:** Abril 2026  
**Estado:** Completo

---

## 1. INTRODUCCIÓN

### 1.1 Propósito
Este documento especifica los requisitos funcionales y no-funcionales del sistema PIXARTEK, un sistema de retroalimentación visual interactivo para actividades de pintura guiada en espacios de exposición o educativos.

### 1.2 Alcance
PIXARTEK es un sistema de pintura participativa que:
- Permite usuarios pintar artesanías en un lienzo mediante etapas guiadas
- Proporciona retroalimentación visual en tiempo real sobre precisión y técnica
- Utiliza análisis de visión por computadora para validar el progreso del usuario
- Controla automáticamente la dispensación de pigmentos
- Proyecta imágenes de referencia para guiar el proceso

### 1.3 Definiciones, Acrónimos y Abreviaturas

| Término | Definición |
|---------|-----------|
| **RPI** | Raspberry Pi (minicomputadora) |
| **MQTT** | Message Queuing Telemetry Transport (protocolo de messaging) |
| **WebSocket** | Protocolo de comunicación bidireccional en tiempo real |
| **OpenCV** | Biblioteca de visión por computadora |
| **GPIO** | General Purpose Input/Output (pines de control de hardware) |
| **DFD** | Data Flow Diagram |
| **PWM** | Pulse Width Modulation (para control de motor) |
| **UI/UX** | User Interface / User Experience |
| **API** | Application Programming Interface |
| **REST** | Representational State Transfer |

### 1.4 Estructura del Documento
- Requisitos Funcionales
- Requisitos No-Funcionales
- Casos de Uso
- Restricciones
- Supuestos y Dependencias

---

## 2. REQUISITOS FUNCIONALES

### 2.1 Gestión de Catálogo de Obras

#### RF 2.1.1: Visualizar Catálogo de Artworks
**Descripción:** El sistema debe permitir a los usuarios visualizar una lista completa de obras de arte disponibles para pintar.

**Actores:** Usuario Final

**Precondiciones:** 
- Frontend está operativo
- Base de datos contiene al menos 1 artwork

**Flujo Principal:**
1. Usuario accede a la página de catálogo
2. Sistema carga lista de artworks desde Backend API
3. Cada artwork muestra: título, artista, dificultad, duración estimada, imagen thumbnail
4. Lista es interactiva y filtrable

**Postcondiciones:**
- Catálogo se muestra en la interfaz
- Usuario puede seleccionar una obra

**Criterios de Aceptación:**
- ✓ Mínimo 4 obras disponibles
- ✓ Carga en menos de 2 segundos
- ✓ Imágenes se renderizan correctamente
- ✓ Información es legible y clara

---

#### RF 2.1.2: Gestionar Metadata de Artworks
**Descripción:** Sistema debe almacenar y recuperar información de cada artwork.

**Datos a Almacenar:**
- id, título, artista, año
- Dificultad (beginner/intermediate/advanced)
- Duración total en minutos
- Color de fondo
- URL de imagen
- Tags descriptivos
- Array de etapas (stages)

**API Endpoint:**
```
GET /api/artworks
GET /api/artworks/{artwork_id}
```

---

### 2.2 Gestión de Sesiones de Pintura

#### RF 2.2.1: Crear Nueva Sesión
**Descripción:** Usuario inicia una sesión de pintura en un artwork específico.

**Actores:** Usuario, Backend, MQTT Broker

**Precondiciones:**
- Artwork seleccionado
- Backend operativo
- MQTT Broker disponible

**Flujo Principal:**
1. Usuario hace click en "Empezar" en catálogo
2. Frontend envía POST /api/sessions con {artwork_id, start_stage, total_stages}
3. Backend crea registro en base de datos
4. Backend publica comando de proyección a MQTT
5. Vision Node recibe comando y se prepara para análisis
6. Proyector muestra imagen de referencia de Stage 1
7. Session page se abre

**Datos Creados:**
```json
{
  "session_id": "uuid",
  "artwork_id": "string",
  "start_stage": 1,
  "current_stage": 1,
  "total_stages": 4,
  "created_at": "timestamp",
  "status": "active"
}
```

**Criterios de Aceptación:**
- ✓ Sesión se crea en < 1 segundo
- ✓ Proyector muestra referencia inmediatamente
- ✓ Vision Node se sincroniza con stage
- ✓ Frontend refleja estado actual

---

#### RF 2.2.2: Avanzar a Siguiente Etapa
**Descripción:** Usuario puede pasar a la siguiente etapa de la obra.

**Requisitos:**
- User presses "Next Stage" button
- Current stage < total_stages
- Session remain activo

**Flujo:**
1. Frontend: PATCH /api/sessions/{session_id}/stage {stage: current_stage + 1}
2. Backend: Incrementa etapa en DB
3. Backend: MQTT Publish → projection/command (nueva etapa)
4. Vision Node: Carga nueva imagen de referencia
5. Projector: Muestra nueva referencia
6. Frontend: Actualiza UI

**Criterios de Aceptación:**
- ✓ Transición < 500ms
- ✓ Nueva referencia se despliega
- ✓ Vision Node sincronizado
- ✓ Métricas se resetean para nueva etapa

---

#### RF 2.2.3: Registrar Sesión Completa
**Descripción:** Sistema registra métricas finales cuando usuario completa todas las etapas.

**Datos a Registrar:**
- Total de tiempo empleado
- Precisión promedio por etapa
- Desviación de color promedio
- Errores detectados
- Sugerencias generadas

---

### 2.3 Retroalimentación Visual en Tiempo Real

#### RF 2.3.1: Capturar y Analizar Frames de Cámara
**Descripción:** Vision Node debe capturar frames de la cámara USB y analizarlos contra la referencia.

**Requisitos Técnicos:**
- Captura: Cada ~2 segundos
- Resolución: Mínimo 640x480
- Frame procesado < 1 segundo

**Análisis Requerido:**
- Precision %: Porcentaje de píxeles que coinciden con referencia
- Color Deviation: Delta-E entre colores esperados y reales
- Stroke Errors: Zonas en grid 3x3 con desviaciones
- Suggestions: Tips accionables para mejorar

**Fórmulas:**
```
Precision % = (matching_pixels / total_pixels) * 100

Color Deviation = sqrt((L1-L2)² + (a1-a2)² + (b1-b2)²)
  donde L,a,b son coordenadas de color Lab

Stroke Error Zone = if(local_precision < 70%) then ERROR
```

**Criterios de Aceptación:**
- ✓ Análisis completa en < 1 segundo
- ✓ Precision % es reproducible (±2%)
- ✓ Detección de errores con 85%+ accuracy
- ✓ No genera falsos positivos

---

#### RF 2.3.2: Publicar Feedback en Tiempo Real
**Descripción:** Vision Node publica feedback a MQTT para broadcast a todos los clientes.

**Estructura de Mensaje MQTT:**
```json
{
  "topic": "pixartek/vision/feedback",
  "payload": {
    "node": "rpi4-vision",
    "artwork_id": "string",
    "stage": 1,
    "precision_pct": 85.5,
    "color_deviation": 12.3,
    "stroke_errors": [
      {
        "zone": "superior-izquierda",
        "message": "Falta más rojo en esta área"
      }
    ],
    "suggestions": [
      "Buen progreso en los tonos principales",
      "Intenta mezclar más los bordes"
    ],
    "timestamp": 1234567890
  }
}
```

**Frecuencia:** Cada ~2 segundos mientras está activa la sesión

---

#### RF 2.3.3: Mostrar Overlay de Feedback
**Descripción:** Frontend muestra overlay visual con feedback inmediato.

**Tipos de Feedback:**
1. **Correcto**: ✓ Verde - Área pintada correctamente
2. **Sugerencia**: 💡 Amarillo - Tips para mejorar
3. **Corrección**: ⚠️ Rojo - Área necesita corrección

**Comportamiento:**
- Aparece por 4 segundos
- Auto-cierra con sonido
- Actualiza en tiempo real
- Muestra zona específica del grid 3x3

**Criterios de Aceptación:**
- ✓ Overlay aparece < 200ms de recibir feedback
- ✓ Sonido plays correctamente
- ✓ No interfiere con experiencia de usuario
- ✓ Actualiza sin lag perceptible

---

### 2.4 Control de Hardware

#### RF 2.4.1: Controlar Dispensador de Pigmento
**Descripción:** Backend puede controlar dispensador de pintura automáticamente.

**Requisitos:**
- Puerto GPIO configurable
- Control PWM para velocidad variable
- Duración en milisegundos

**API Endpoint:**
```
POST /api/hardware/dispense
Body: {
  "pigment_slot": 1,
  "duration_ms": 500
}
```

**Criterios de Aceptación:**
- ✓ Dispensa cantidad consistente
- ✓ Tarda < 1 segundo en ejecutar
- ✓ Responde a comandos < 100ms
- ✓ Safety: Auto-stop después de 5 segundos

---

#### RF 2.4.2: Controlar Proyector
**Descripción:** Projection Node controla qué imagen se proyecta según etapa.

**Requisitos:**
- Recibe comando MQTT con etapa
- Carga imagen de referencia desde filesystem
- Proyecta a pantalla HDMI/conexión disponible

**Imágenes Requeridas:**
- Una por etapa por artwork
- Resolución: 1280x720 mínimo
- Formato: PNG
- Ruta: `/artworks/{artwork_id}/{stage_image}`

---

### 2.5 Gestión de Métricas

#### RF 2.5.1: Registrar Métricas de Sesión
**Descripción:** Sistema registra métricas de desempeño para cada etapa.

**Datos a Registrar:**
```json
{
  "session_id": "uuid",
  "stage": 1,
  "precision_pct": 85.5,
  "color_deviation": 12.3,
  "elapsed_s": 120,
  "feedback_json": {
    "errors": [...],
    "suggestions": [...]
  },
  "recorded_at": "timestamp"
}
```

**API Endpoint:**
```
POST /api/sessions/{session_id}/metrics
```

**Criterios de Aceptación:**
- ✓ Métricas se guardan < 100ms
- ✓ Sin pérdida de datos
- ✓ Indexadas por session_id y stage

---

### 2.6 Gestión de Perfiles de Usuario

#### RF 2.6.1: Seleccionar Perfil
**Descripción:** Sistema permite seleccionar perfil antes de sesión.

**Datos de Perfil:**
- Nombre
- Avatar (opcional)
- ID único

**Almacenamiento:** Local Storage del navegador

---

## 3. REQUISITOS NO-FUNCIONALES

### 3.1 Performance

#### RNF 3.1.1: Tiempo de Respuesta
- API endpoints: < 200ms
- WebSocket messages: < 100ms
- Análisis de visión: < 1 segundo
- Carga de página: < 2 segundos

#### RNF 3.1.2: Throughput
- MQTT: 10+ mensajes/segundo
- Simultaneous WebSocket connections: 50+
- Vision Node: Procesa 1 frame cada 2 segundos

### 3.2 Disponibilidad y Confiabilidad

#### RNF 3.2.1: Uptime
- Backend: 99.5% uptime objetivo
- Frontend: 99.9% (browser-based)
- MQTT Broker: 99.5% uptime

#### RNF 3.2.2: Recuperación de Errores
- Reconexión automática en case de desconexión MQTT
- Reintentos de API con backoff exponencial
- Fallback a métricas predefinidas si Vision falla

### 3.3 Escalabilidad

#### RNF 3.3.1: Capacidad
- Soportar 100+ sesiones simultáneas
- 1000+ artworks en catálogo
- Crecer a 3+ nodos de visión sin rediseño

### 3.4 Seguridad

#### RNF 3.4.1: Control de Acceso
- CORS habilitado (permitir front-end)
- No requiere autenticación (sistema público/educativo)
- GPIO protegido (solo Backend puede controlar)

#### RNF 3.4.2: Protección de Datos
- Database encriptada en reposo (SQLite journal)
- MQTT sin credenciales (red interna privada)
- No almacena datos personales sensibles

### 3.5 Usabilidad

#### RNF 3.5.1: Interfaz
- Responsive en tablets (1024x768 mínimo)
- Touch-friendly buttons (48px mínimo)
- Colores accesibles (WCAG AA)
- Lenguaje claro en español

#### RNF 3.5.2: Accesibilidad
- Alt text para imágenes
- Contraste mínimo 4.5:1
- Soporte para keyboard navigation

### 3.6 Mantenibilidad

#### RNF 3.6.1: Código
- TypeScript para type safety
- Modularidad: Componentes reutilizables
- Documentación: Código comentado
- Tests: Coverage >70% en lógica crítica

#### RNF 3.6.2: Deployment
- Docker-ready (si aplica)
- Scripts de setup automatizados
- Configuración por environment variables

### 3.7 Compatibilidad

#### RNF 3.7.1: Hardware
- Raspberry Pi 5 (principal)
- Raspberry Pi 4 B y 4 A (nodos)
- Cámaras USB estándar
- Proyectores HDMI

#### RNF 3.7.2: Software
- Python 3.9+
- Node.js 18+
- Navegadores modernos (Chrome, Firefox, Safari)

---

## 4. CASOS DE USO

### UC-1: Pintar una Obra Completa

**Actor Principal:** Usuario

**Precondiciones:**
- Sistema operativo y listo
- Catálogo visible
- Hardware disponible

**Flujo Principal:**
1. Usuario abre aplicación
2. Ve catálogo de obras
3. Selecciona una obra (ej. "Flores Blancas")
4. Elige dificultad/perfil
5. Inicia sesión
6. Ve Stage 1 proyectado
7. Pinta según referencia
8. Recibe feedback en tiempo real:
   - Precisión %
   - Colores correctos/incorrectos
   - Sugerencias
9. Avanza a Stage 2
10. Repite para todas las etapas
11. Completa obra
12. Ve resumen de desempeño

**Postcondiciones:**
- Sesión guardada en BD
- Métricas registradas
- Usuario regresa a catálogo

---

### UC-2: Recibir Feedback Visual en Tiempo Real

**Actor Principal:** Usuario

**Precondiciones:**
- Sesión activa
- Vision Node operativo
- Cámara conectada

**Flujo:**
1. Usuario pinta
2. Cámara captura frame cada 2 segundos
3. Vision Node analiza
4. Feedback publicado a MQTT
5. Backend broadcast a WebSocket
6. Frontend recibe mensaje
7. Overlay aparece con:
   - Tipo de feedback (correcto/sugerencia/corrección)
   - Mensaje específico
   - Zona donde ocurre
8. Sonido notifica al usuario
9. Overlay desaparece en 4 segundos

**Variantes:**
- Sin feedback: Primer frame, o no hay diferencia
- Multiple overlays: Se queue y muestran secuencialmente

---

### UC-3: Administrador Añade Nueva Obra

**Actor Principal:** Sistema Administrator

**Precondiciones:**
- Acceso al servidor backend
- Imágenes de referencia preparadas

**Flujo:**
1. Admin prepara 4-5 imágenes de etapas
2. Crea entrada en ARTWORKS array en seed.py
3. Ingresa metadata: título, artista, descripción, duración
4. Define colores y materiales para cada etapa
5. Reinicia backend
6. Obra aparece en catálogo

---

### UC-4: Vision Node Falla

**Actor Principal:** Sistema (manejo de error)

**Precondiciones:**
- Sesión activa
- Vision Node se desconecta (red, crash, etc.)

**Flujo:**
1. Vision Node para de publicar feedback
2. Backend espera ~5 segundos
3. Frontend detecta ausencia de mensajes
4. Muestra alerta: "Sistema de visión no disponible"
5. Usuario puede continuar pintando (modo manual)
6. Metrics se registran pero sin vision feedback
7. Si Vision vuelve, continúa análisis

---

## 5. RESTRICCIONES

### 5.1 Restricciones Técnicas
- Sistema debe ejecutarse en Raspberry Pi (recursos limitados)
- Comunicación entre nodos solo via MQTT (sin TCP directo)
- Cámara debe estar a distancia operativa (0.5-2m)
- Proyector debe estar visibles al usuario

### 5.2 Restricciones Funcionales
- Máximo 5 etapas por obra (limitación UI)
- Imágenes deben estar en filesystem local
- Análisis de visión requiere buena iluminación
- Una sesión por usuario simultáneamente (diseño actual)

### 5.3 Restricciones de Negocio
- Sistema diseñado para uso educativo/exhibición
- No requiere autenticación (público)
- Datos de sesión se guardan (auditoría)
- No hay suscripción/pago

---

## 6. SUPUESTOS Y DEPENDENCIAS

### 6.1 Supuestos
- Red WiFi interna confiable (< 50ms latencia)
- Hardware físico funcional (proyector, cámara, RPI)
- Iluminación ambiental adecuada para captura de cámara
- Usuarios entienden instrucciones básicas en español

### 6.2 Dependencias Externas
- **Mosquitto**: MQTT broker (instalado en RPI5)
- **OpenCV**: Biblioteca de visión (instalada en RPI4-B)
- **FastAPI**: Framework web (Python RPI5)
- **Next.js**: Framework frontend (Node.js RPI5)
- **SQLite**: Database (integrado, no requiere instalación separada)

### 6.3 Dependencias Internas
- Vision Node depende de conexión MQTT
- Frontend depende de Backend API
- Projection Node depende de comando MQTT
- Todos dependen del Hardware (cámara, proyector, RPI)

---

## 7. CRITERIOS DE ACEPTACIÓN GENERAL

El sistema se considera completo cuando:

- [ ] Todas las obras del catálogo son pintables
- [ ] Feedback visual aparece en < 200ms
- [ ] Vision Node analiza cada frame en < 1 segundo
- [ ] Sesión se crea en < 1 segundo
- [ ] No hay pérdida de datos de métricas
- [ ] Interface es intuitiva (5/5 stars en usabilidad)
- [ ] Sistema mantiene 99.5% uptime en 1 semana de operación
- [ ] 4+ obras cargadas por defecto
- [ ] Manejo gracioso de fallos de hardware

---

## 8. MATRIZ DE TRAZABILIDAD

| Req ID | Descripción | Módulo | Estado |
|--------|-------------|--------|--------|
| RF 2.1.1 | Visualizar catálogo | Frontend/Backend | ✅ Completo |
| RF 2.2.1 | Crear sesión | Backend | ✅ Completo |
| RF 2.2.2 | Avanzar etapa | Backend/Frontend | ✅ Completo |
| RF 2.3.1 | Capturar frames | Vision Node | ✅ Completo |
| RF 2.3.2 | Publicar feedback | Vision Node/Backend | ✅ Completo |
| RF 2.3.3 | Mostrar overlay | Frontend | ✅ Completo |
| RF 2.4.1 | Controlar pigmento | Backend/GPIO | ✅ Completo |
| RF 2.4.2 | Controlar proyector | Projection Node | ✅ Completo |
| RF 2.5.1 | Registrar métricas | Backend | ✅ Completo |
| RNF 3.1.1 | Performance API | Backend | ✅ Cumple |
| RNF 3.2.1 | Uptime 99.5% | DevOps | ⏳ Monitoreando |
| RNF 3.4.1 | Seguridad | Todo | ✅ Cumple |

---

**Fin del Documento de Especificación de Requisitos**
