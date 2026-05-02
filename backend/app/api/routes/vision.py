"""Vision Node endpoints — camera feed and analysis."""
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
import io
import json
import paho.mqtt.client as mqtt
import threading
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["vision"])

# Store last camera frame and metadata
_camera_frame_data = {
    "frame": None,  # JPEG bytes
    "timestamp": None,
    "lock": threading.Lock(),
}

def _start_camera_listener():
    """Subscribe to vision node camera frame topic and store latest frame."""
    def on_message(client, userdata, msg):
        try:
            if msg.topic == "pixartek/vision/camera-frame":
                with _camera_frame_data["lock"]:
                    _camera_frame_data["frame"] = msg.payload
                    _camera_frame_data["timestamp"] = time.time()
                logger.debug(f"Camera frame received: {len(msg.payload)} bytes")
        except Exception as e:
            logger.error(f"Error processing camera frame: {e}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message

    try:
        client.connect("localhost", 1883, 60)
        client.subscribe("pixartek/vision/camera-frame")
        client.loop_start()
        logger.info("Camera frame listener started")
    except Exception as e:
        logger.error(f"Failed to start camera listener: {e}")


# Start listener in background
_listener_thread = threading.Thread(target=_start_camera_listener, daemon=True)
_listener_thread.start()


@router.get("/camera-frame")
async def get_camera_frame():
    """
    Get the latest camera frame captured by the vision node.
    Returns a JPEG image of what the camera is currently observing.
    """
    with _camera_frame_data["lock"]:
        if _camera_frame_data["frame"] is None:
            # Return a placeholder image if no frame available
            return Response(
                content=_generate_placeholder_image(),
                media_type="image/jpeg"
            )

        return Response(
            content=_camera_frame_data["frame"],
            media_type="image/jpeg"
        )


@router.get("/camera-frame/test")
async def get_test_camera_frame():
    """
    Get a test camera frame for demonstration purposes.
    Shows what the camera feed area will look like.
    """
    return Response(
        content=_generate_test_frame(),
        media_type="image/jpeg"
    )


def _generate_test_frame():
    """Generate a test frame showing the vision analysis canvas."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io

        # Create a canvas-like test frame
        width, height = 320, 240
        img = Image.new('RGB', (width, height), color=(220, 215, 210))  # Canvas color
        draw = ImageDraw.Draw(img)

        # Draw a reference area with the projected image outline
        margin = 20
        draw.rectangle([(margin, margin), (width-margin, height-margin)],
                      outline=(150, 140, 130), width=2)

        # Draw some mock content
        draw.line([(50, 100), (270, 100)], fill=(100, 50, 50), width=2)  # Mock stroke
        draw.line([(100, 60), (150, 140)], fill=(100, 50, 50), width=2)
        draw.ellipse([(120, 80), (180, 140)], outline=(100, 50, 50), width=2)

        # Add grid overlay to show analysis zones
        for x in range(0, width, width//3):
            draw.line([(x, margin), (x, height-margin)], fill=(200, 200, 200), width=1)
        for y in range(0, height, height//3):
            draw.line([(margin, y), (width-margin, y)], fill=(200, 200, 200), width=1)

        # Add status text
        draw.text((160, 10), "Camera Feed", fill=(50, 50, 50), anchor="mm")
        draw.text((160, 230), "Vision OK", fill=(50, 200, 50), anchor="mm")

        # Convert to JPEG
        jpeg_buffer = io.BytesIO()
        img.save(jpeg_buffer, format='JPEG', quality=85)
        return jpeg_buffer.getvalue()
    except Exception as e:
        logger.error(f"Failed to generate test frame: {e}")
        return _generate_placeholder_image()


def _generate_placeholder_image():
    """Generate a simple placeholder image when camera frame is not available."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        # Create a simple image with text
        img = Image.new('RGB', (320, 240), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw center crosshair
        center_x, center_y = 160, 120
        draw.line([(center_x - 30, center_y), (center_x + 30, center_y)], fill=(100, 100, 100), width=2)
        draw.line([(center_x, center_y - 30), (center_x, center_y + 30)], fill=(100, 100, 100), width=2)

        # Draw rectangle to show canvas area
        draw.rectangle([(40, 40), (280, 200)], outline=(100, 100, 100), width=2)

        # Add text
        text = "Esperando\nfotograma\nde camara"
        draw.text((160, 110), text, fill=(100, 100, 100), anchor="mm")

        # Convert to JPEG bytes
        jpeg_buffer = io.BytesIO()
        img.save(jpeg_buffer, format='JPEG', quality=85)
        return jpeg_buffer.getvalue()
    except Exception as e:
        logger.error(f"Failed to generate placeholder: {e}")
        # Return a minimal JPEG if PIL fails
        return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd4\xff\xd9'
