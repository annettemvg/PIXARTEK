"""
PIXARTEK Vision Server
Ejecuta en el Pi de visión (.244). Captura video, analiza pintura,
y envía feedback vía MQTT a pixartek/vision/feedback
"""
import cv2
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
import paho.mqtt.client as mqtt
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("VisionServer")

class VisionServer:
    def __init__(self, mqtt_host: str = "localhost", mqtt_port: int = 1883):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        self.camera = None
        self.reference_image = None
        self.current_artwork_id = None
        self.current_stage = None
        self.running = False

    def connect_mqtt(self):
        """Connect to MQTT broker."""
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message

        try:
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            logger.info(f"Connected to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
            return True
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            return False

    def _on_mqtt_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("MQTT connected successfully")
            client.subscribe("pixartek/vision/command")
        else:
            logger.warning(f"MQTT connect failed with code {rc}")

    def _on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT commands."""
        try:
            payload = json.loads(msg.payload.decode())
            if msg.topic == "pixartek/vision/command":
                if payload.get("action") == "set_reference":
                    self.load_reference(payload.get("image_path"))
                    self.current_artwork_id = payload.get("artwork_id")
                    self.current_stage = payload.get("stage")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def load_reference(self, image_path: str) -> bool:
        """Load the reference image for the current stage."""
        try:
            self.reference_image = cv2.imread(image_path)
            if self.reference_image is None:
                logger.error(f"Could not load reference: {image_path}")
                return False
            logger.info(f"Reference loaded: {image_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading reference: {e}")
            return False

    def initialize_camera(self, camera_index: int = 0) -> bool:
        """Initialize camera capture."""
        try:
            self.camera = cv2.VideoCapture(camera_index)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            logger.info(f"Camera initialized (index {camera_index})")
            return True
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            return False

    def analyze_frame(self, frame: np.ndarray) -> dict:
        """Analyze a frame against the reference."""
        if self.reference_image is None:
            return None

        try:
            ref_h, ref_w = self.reference_image.shape[:2]
            frame_resized = cv2.resize(frame, (ref_w, ref_h))

            frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
            ref_gray = cv2.cvtColor(self.reference_image, cv2.COLOR_BGR2GRAY)

            _, frame_bin = cv2.threshold(frame_gray, 127, 255, cv2.THRESH_BINARY)
            _, ref_bin = cv2.threshold(ref_gray, 127, 255, cv2.THRESH_BINARY)

            diff = cv2.bitwise_xor(frame_bin, ref_bin)
            error_pixels = cv2.countNonZero(diff)
            total_pixels = frame_bin.size
            error_rate = error_pixels / total_pixels

            frame_hsv = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2HSV)
            ref_hsv = cv2.cvtColor(self.reference_image, cv2.COLOR_BGR2HSV)
            color_diff = cv2.absdiff(frame_hsv, ref_hsv)
            color_deviation = np.mean(color_diff)

            precision_pct = max(0, 100 - (error_rate * 100))

            stroke_errors = []
            suggestions = []

            if error_rate > 0.20:
                stroke_errors.append({
                    "zone": "general",
                    "message": "Hay diferencias importantes. Revisa los contornos y rellenos."
                })
            elif error_rate > 0.10:
                stroke_errors.append({
                    "zone": "general",
                    "message": "Faltan algunos detalles. Continúa refinando."
                })

            if color_deviation > 35:
                suggestions.append("Ajusta los colores. Mezcla más cuidadosamente los pigmentos.")
            elif color_deviation > 20:
                suggestions.append("Los colores están cerca. Refina un poco más.")

            return {
                "precision_pct": precision_pct,
                "color_deviation": float(color_deviation),
                "stroke_errors": stroke_errors,
                "suggestions": suggestions,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Frame analysis error: {e}")
            return None

    def publish_feedback(self, feedback: dict):
        """Publish feedback to MQTT."""
        if self.mqtt_client and feedback:
            try:
                self.mqtt_client.publish(
                    "pixartek/vision/feedback",
                    json.dumps(feedback),
                    qos=1
                )
                logger.info(f"Feedback published: precision={feedback['precision_pct']:.1f}%")
            except Exception as e:
                logger.error(f"Error publishing feedback: {e}")

    async def run(self):
        """Main loop: capture and analyze frames."""
        self.running = True
        frame_count = 0

        while self.running:
            if not self.camera:
                await asyncio.sleep(1)
                continue

            ret, frame = self.camera.read()
            if not ret:
                logger.warning("Failed to read frame")
                await asyncio.sleep(0.1)
                continue

            frame_count += 1
            if frame_count % 5 == 0:
                feedback = self.analyze_frame(frame)
                if feedback:
                    self.publish_feedback(feedback)

            await asyncio.sleep(0.03)

    def shutdown(self):
        """Clean shutdown."""
        self.running = False
        if self.camera:
            self.camera.release()
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        logger.info("Vision server shut down")

async def main():
    server = VisionServer(mqtt_host="192.168.86.243", mqtt_port=1883)

    if not server.connect_mqtt():
        logger.error("Failed to connect to MQTT")
        return

    if not server.initialize_camera(0):
        logger.error("Failed to initialize camera")
        return

    logger.info("Vision server started. Waiting for reference image...")

    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        server.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
