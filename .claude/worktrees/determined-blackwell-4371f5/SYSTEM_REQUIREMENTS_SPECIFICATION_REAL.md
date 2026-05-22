# PIXARTEK - System Requirements Specification (SRS) - VERSIÓN REAL
**Versión:** 2.0  
**Fecha:** Abril 2026  
**Estado:** Basado en Especificación Física Real  
**Fuente:** SISTEMAS DE PIXARTEK.pdf

---

## 1. INTRODUCCIÓN

### 1.1 Propósito
Este documento especifica los requisitos funcionales y no-funcionales del sistema PIXARTEK, un **robot dispensador de pintura con retroalimentación visual en tiempo real**, capaz de automatizar la aplicación de colores en una paleta de 6 compartimentos, con monitoreo por visión artificial y guías de proyección.

### 1.2 Alcance del Sistema
PIXARTEK es un sistema robótico integrado que:
- Dispensa pintura automáticamente en 6 pozos de una paleta mediante bombas peristálticas
- Posiciona con precisión las boquillas de dispensación usando un actuador lineal con motor stepper
- Monitorea el progreso mediante visión artificial en tiempo real
- Proyecta guías visuales de referencia en el lienzo del usuario
- Proporciona limpieza automática de pinceles
- Coordina todas las acciones a través de una interfaz de control centralizada

### 1.3 Componentes Principales del Sistema

**Hardware:**
- 1 Raspberry Pi 5 (Control Central)
- 2 Raspberry Pi 4 (Visión + Proyección)
- 5 Bombas Peristálticas
- 1 Actuador Lineal con Motor Stepper
- 1 Proyector Caydo P1
- 1 Cámara CSI
- 1 Bomba Sumergible (Limpieza)
- Múltiples controladores y sensores

**Software:**
- Application de control en Raspberry Pi 5
- Software de visión artificial en Raspberry Pi 4
- Software de proyección sincronizado

---

## 2. REQUISITOS FUNCIONALES

### 2.1 Sistema de Pintura Automática

#### RF 2.1.1: Dispensación de Pintura en Múltiples Colores
**Descripción:** El sistema debe dispensar automáticamente pintura en cada uno de los 6 pozos de la paleta mediante bombas peristálticas controladas.

**Componentes Involucrados:**
- 5 Bombas Peristálticas (controladas por L298N)
- 5 Envases de Pintura (almacenamiento)
- 10 Mangueras de Suero (distribución)
- Paleta de Pintura (6 compartimentos)

**Requisitos Técnicos:**
- Capacidad: Dispensar hasta 5 colores diferentes
- Precisión: ±5% del volumen especificado
- Velocidad: Dispensación completa en < 2 minutos
- Sin contaminación cruzada entre colores
- Control de flujo mediante boquillas calibradas

**Flujo de Proceso:**
1. Usuario selecciona colores desde pantalla
2. RPI5 calcula tiempo de dispensación por color
3. RPI5 envía señal a controlador L298N
4. Bomba peristáltica activa según duración especificada
5. Pintura fluye a través de mangueras hacia boquilla
6. Boquilla deposita pintura en pozo específico
7. Proceso se repite para cada color

**Criterios de Aceptación:**
- ✓ Dispensación uniforme en cada pozo
- ✓ Sin derrames ni goteos
- ✓ Pintura mantiene viscosidad óptima
- ✓ Boquillas no obstruidas tras uso
- ✓ Variación < 5% entre dispensaciones

---

#### RF 2.1.2: Posicionamiento Automático mediante Actuador Lineal
**Descripción:** Sistema debe posicionar automáticamente las mangueras sobre cada pozo usando un actuador lineal controlado por motor stepper.

**Componentes:**
- 1 Actuador Lineal con Motor Stepper
- 1 Controlador TMC2209
- 2 Sensores de Límite (inicio/fin de carrera)

**Requisitos:**
- Movimiento horizontal suave sin vibraciones
- Posicionamiento preciso en cada uno de 6 pozos
- Velocidad de movimiento: ~2 segundos entre pozos
- Detección automática de límites
- Prevención de sobre-movimiento

**Especificaciones Técnicas:**
- Motor: NEMA 17 o equivalente
- Controlador: TMC2209 (microstepping)
- Sensores: Interruptores de final de carrera (NO)
- Recorrido: Aproximadamente 300-400mm

**Flujo de Control:**
1. RPI5 calcula posición objetivo (1-6)
2. RPI5 envía comando a TMC2209
3. Motor stepper mueve actuador linealmente
4. Sensores de límite detectan posiciones extremas
5. RPI5 verifica posición mediante encoder (si aplica)
6. Sistema confirma posicionamiento correcto

---

#### RF 2.1.3: Control de Fuentes de Poder
**Descripción:** Sistema debe gestionar múltiples fuentes de poder para diferentes subsistemas sin conflictos.

**Fuentes Requeridas:**
- (4) Fuentes de 12V para bombas peristálticas
- (1) Fuente de 12V para actuador lineal
- (1) Fuente de 5V Tipo-C para RPI5
- Independencia entre fuentes

---

### 2.2 Sistema de Limpieza de Pinceles

#### RF 2.2.1: Limpieza Automática Activada por Proximidad
**Descripción:** Sistema debe activar automáticamente la limpieza de pinceles cuando se detecta proximidad.

**Componentes:**
- 1 Bomba Sumergible
- 1 Sensor Infrarrojo de Proximidad
- 1 Envase de Almacenamiento (agua limpia)
- 1 Envase Pequeño (lavadora con agua de entrada)
- 1 Envase de Drenaje (agua sucia)

**Requisitos:**
- Detección de proximidad de pincel: 0-30cm
- Activación automática de bomba
- Caudal de agua: ~2-3 litros/minuto
- Distribución uniforme mediante sistema de riego

**Sistema de Tuberías:**
- Tubo PVC rígido (conducción principal)
- Codos PVC (cambios de dirección)
- Adaptador cinta riego pluvio (distribución amplia)
- Manguera ducha flexible (aplicación final)

**Flujo de Proceso:**
1. Sensor detecta pincel a distancia < 30cm
2. Sensor envía señal a RPI5 (GPIO)
3. RPI5 energiza bomba sumergible
4. Agua es bombeada desde envase de almacenamiento
5. Agua fluye a través de sistema de tuberías
6. Manguera ducha distribuye agua como lluvia
7. Agua sucia se drena al envase de drenaje
8. Sensor deja de detectar → bomba se detiene

**Criterios de Aceptación:**
- ✓ Activación automática dentro de 500ms
- ✓ Agua limpia sin contaminantes visibles
- ✓ Cobertura completa del pincel
- ✓ Sistema de drenaje sin derrames
- ✓ Ciclo completo < 30 segundos

---

### 2.3 Sistema de Visión Artificial

#### RF 2.3.1: Captura y Análisis de Video en Tiempo Real
**Descripción:** Monitorear el lienzo mediante visión artificial para análisis del progreso artístico.

**Componentes:**
- 1 Raspberry Pi 4 (procesamiento)
- 1 Cámara CSI (captura)
- 1 Sistema de Montaje Ajustable

**Requisitos Técnicos:**
- Resolución mínima: 1920x1080p
- Frame rate: 30 FPS mínimo
- Latencia: < 100ms de captura a análisis
- Ajustabilidad de posición y ángulo

**Capacidades Analíticas:**
- Detección de cobertura (% de área pintada)
- Análisis de color (precisión de color vs. referencia)
- Detección de áreas no pintadas
- Seguimiento de progreso etapa por etapa

**Flujo de Operación:**
1. Cámara captura frames continuamente (30 FPS)
2. RPI4 recibe stream de video vía CSI
3. Software de visión analiza cada frame
4. Compara contra imagen de referencia
5. Calcula métricas (cobertura, color, errores)
6. Envía resultados a RPI5 vía red/MQTT
7. RPI5 actualiza UI con feedback

---

### 2.4 Sistema de Proyección

#### RF 2.4.1: Proyección Sincronizada de Guías Visuales
**Descripción:** Proyectar guías y referencias directamente en el lienzo para guiar al usuario.

**Componentes:**
- 1 Proyector Caydo P1
- 1 Raspberry Pi 4 (control)
- 1 Estructura Fija de Precisión
- 1 Lienzo
- 2 Caballetes

**Requisitos:**
- Proyección sin distorsión
- Sincronización con etapa actual
- Brillo suficiente para visibilidad diurna
- Precisión de posicionamiento ± 5mm

**Imágenes a Proyectar:**
- Trazos de referencia (líneas guía)
- Áreas de color (zonas específicas por color)
- Números de etapa (progreso)
- Instrucciones de usuario

**Flujo de Control:**
1. Usuario inicia sesión de pintura
2. RPI5 comunica etapa actual a RPI4 (proyección)
3. RPI4 carga imagen de referencia para etapa N
4. Proyector Caydo P1 muestra imagen en lienzo
5. Usuario pinta siguiendo proyección
6. Cuando usuario avanza a etapa N+1:
   - RPI5 notifica a RPI4
   - RPI4 carga nueva imagen
   - Proyector actualiza en < 500ms

---

### 2.5 Panel de Control de Aplicación

#### RF 2.5.1: Interfaz Gráfica de Usuario (GUI)
**Descripción:** Panel de control táctil que permite al usuario seleccionar colores, ver estado del sistema y controlar el proceso.

**Componentes:**
- 1 Raspberry Pi 5 (procesamiento central)
- 1 Pantalla HDMI táctil
- 1 Cable HDMI (conexión)
- Cables de alimentación (5V USB-C, Micro-USB)

**Funcionalidades Requeridas:**
1. **Selección de Colores**
   - Mostrar 5 opciones de color disponibles
   - Indicador visual de cantidad restante
   - Selección mediante touch

2. **Monitoreo de Estado**
   - Estado de sensores de límite (OK/Error)
   - Nivel de tinta en envases
   - Temperatura de componentes
   - Status de bomba de limpieza

3. **Control Manual**
   - Botón de dispensación manual
   - Botón de limpieza de pinceles
   - Botón de emergencia (STOP)
   - Control de velocidad de actuador

4. **Indicadores Visuales**
   - LED de sistema activo
   - Código de colores para estado
   - Progreso de tarea actual
   - Alertas de error

**Especificaciones de Pantalla:**
- Tipo: HDMI táctil resistiva o capacitiva
- Resolución: 1280x720 mínimo
- Tamaño: 7-10 pulgadas recomendado
- Respuesta táctil: < 100ms

---

### 2.6 Requisitos de Coordinación

#### RF 2.6.1: Secuencia de Operación Completa
**Descripción:** Sistema debe ejecutar secuencia coordinada de operaciones.

**Flujo Típico:**
```
1. Usuario selecciona proyecto desde pantalla
2. RPI5 carga configuración (colores, tiempos, posiciones)
3. RPI5 inicializa actuador a posición HOME (sensor de límite)
4. RPI5 comunica a RPI4 (visión y proyección) que inicie
5. RPI4-Vision captura baseline de lienzo vacío
6. RPI4-Proyección muestra guías para color 1
7. Para cada color (1-5):
   a. RPI5 mueve actuador a posición del color
   b. RPI5 activa bomba por tiempo X
   c. Pintura se dispensa en pozo
   d. Usuario pinta siguiendo proyección
   e. RPI4-Vision monitorea progreso
   f. Si cobertura < 80%: mostrar alerta
   g. Cuando listo, usuario avanza a siguiente color
8. Después de todos los colores:
   a. RPI5 retorna actuador a HOME
   b. RPI5 activa sistema de limpieza (sensor próximo)
   c. RPI4 finaliza grabación de sesión
9. Pantalla muestra resumen de sesión
```

---

## 3. REQUISITOS NO-FUNCIONALES

### 3.1 Performance

#### RNF 3.1.1: Tiempo de Respuesta
- Panel táctil: < 100ms respuesta a toque
- Proyector: < 500ms cambio de imagen
- Visión: 30 FPS continuous
- Actuador: Movimiento entre pozos en 2-3 segundos
- Bomba: Activación en < 500ms

#### RNF 3.1.2: Precisión de Dispensación
- Volumen ±5%
- Posicionamiento actuador ±2mm
- Proyección ±5mm en lienzo

### 3.2 Disponibilidad

#### RNF 3.2.1: Tiempo de Funcionamiento
- Uptime objetivo: 99%
- Sesión típica: 15-30 minutos sin interrupciones
- Reinicio del sistema: < 60 segundos

### 3.3 Seguridad

#### RNF 3.3.1: Protecciones de Seguridad
- Botón de emergencia (detiene bombas y actuador)
- Sensores de límite previenen daño mecánico
- Sobrecorriente en controladores L298N
- Aislamiento eléctrico entre circuitos
- No hay riesgo de pintura tóxica en superficies de contacto

### 3.4 Mantenibilidad

#### RNF 3.4.1: Acceso a Componentes
- Todas las bombas accesibles para reemplazo
- Mangueras intercambiables sin herramientas especiales
- Envases de pintura fáciles de llenar/limpiar
- Cámara ajustable sin desmontar estructura

### 3.5 Compatibilidad

#### RNF 3.5.1: Pinturas y Materiales
- Compatible con pintura acrílica de viscosidad controlada
- Mangueras de suero inerte (no reactivo con pigmentos)
- Boquillas calibradas para flujo uniforme

---

## 4. CASOS DE USO

### UC-1: Sesión Completa de Pintura

**Actor:** Usuario Artista

**Precondiciones:**
- Sistema iniciado y pantalla funcionando
- Envases de pintura llenos
- Agua limpia en tanque de limpieza
- Lienzo montado en caballete

**Flujo:**
1. Usuario ve pantalla principal
2. Selecciona proyecto/tema deseado
3. Sistema proyecta guías para Color 1
4. Sistema dispensa Color 1 en pozo
5. Usuario pinta en lienzo siguiendo proyección
6. RPI4-Vision monitorea cobertura
7. Cuando listo, usuario toca "Siguiente"
8. Sistema avanza a Color 2 (pasos 3-7 repetidos)
9. Después de Color 5, sistema inicia limpieza automática
10. Usuario limpia pinceles en estación
11. Sensor infrarrojo activa bomba automáticamente
12. Sistema muestra resumen de sesión completada

**Postcondiciones:**
- Lienzo pintado según patrón
- Pinceles limpios y mojados
- Tanque de drenaje contiene agua sucia
- Sistema listo para nueva sesión

---

### UC-2: Control Manual de Dispensación

**Actor:** Técnico/Operador

**Precondiciones:**
- Sistema iniciado
- Pantalla en modo manual
- Componentes mecánicos verificados

**Flujo:**
1. Operador selecciona "Modo Manual" en pantalla
2. Selecciona color específico
3. Ingresa tiempo de dispensación (segundos)
4. Toca botón "Dispensar"
5. Sistema dispensa por tiempo especificado
6. Operador puede visualizar flujo en tiempo real
7. Repite para diferentes colores según sea necesario

---

### UC-3: Sistema Detiene por Emergencia

**Actor:** Sistema (automático) o Usuario

**Precondiciones:**
- Sistema en operación
- Condición de error detectada O botón presionado

**Flujo:**
1. Sensor detecta condición anormal O usuario presiona STOP
2. RPI5 recibe señal
3. Todas las bombas se detienen inmediatamente
4. Actuador se retrae a posición segura
5. Proyector detiene actualización
6. Pantalla muestra mensaje de error
7. Operador debe diagnosticar antes de reiniciar

---

## 5. RESTRICCIONES

### 5.1 Hardware
- Máximo 5 colores disponibles (limitación física de bombas)
- Paleta fija de 6 compartimentos (no intercambiables)
- Capacidad de lienzo limitada por alcance del actuador
- Proyector requiere distancia mínima para foco

### 5.2 Software
- Sistema operativo: Raspberry Pi OS
- Lenguaje de control: Python 3.9+
- Sin soporte para colores adicionales sin hardware nuevo

### 5.3 Entorno
- Temperatura operativa: 10-40°C
- Humedad: 20-80% (no condensante)
- Iluminación ambiente: para claridad de UI táctil
- Superficie plana para instalación

---

## 6. SUPUESTOS Y DEPENDENCIAS

### 6.1 Supuestos
- Pintura tiene viscosidad compatible con bombeo peristáltico
- Usuario sigue instrucciones de pantalla
- Lienzo montado correctamente en caballetes
- Agua para limpieza reemplazada regularmente
- Mantenimiento preventivo realizado según calendario

### 6.2 Dependencias Externas
- Suministro eléctrico estable (110V)
- Internet (opcional, para logging remoto)
- Software de visión entrenado para referencias específicas

---

## 7. CRITERIOS DE ACEPTACIÓN GENERAL

Sistema se considera completo cuando:

- [ ] Todas las 5 bombas dispensan correctamente
- [ ] Actuador posiciona en todos los 6 pozos sin error
- [ ] Proyector sincroniza con etapas correctamente
- [ ] Visión monitorea cobertura con 85%+ precisión
- [ ] Limpieza automática activa correctamente
- [ ] Panel táctil responde < 100ms
- [ ] Sesión completa ejecuta sin intervención manual
- [ ] Sistema tolera 99% uptime en 48h de operación
- [ ] Documentación completa para mantenimiento

---

**Fin de SRS Real - PIXARTEK**
