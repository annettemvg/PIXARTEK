#!/usr/bin/env bash
# ============================================================
#  PIXARTEK — Setup RPi4-B (Visión + Proyección)
# ============================================================
set -euo pipefail
PIXARTEK_DIR="/home/pi/pixartek"
VISION_DIR="$PIXARTEK_DIR/nodes/vision"
PROJ_DIR="$PIXARTEK_DIR/nodes/projection"

echo "==> [1/7] Actualizando sistema..."
sudo apt-get update -q
sudo apt-get install -y -q \
  python3 python3-venv python3-dev \
  libopencv-dev python3-opencv \
  libcamera-dev \
  python3-picamera2 \
  fbi \
  curl

echo "==> [2/7] Instalando dependencias nodo visión..."
cd "$VISION_DIR"
python3 -m venv .venv --system-site-packages
.venv/bin/pip install -q --upgrade pip
# FastAPI + Uvicorn como servidor de video independiente (sin MQTT)
.venv/bin/pip install -q --prefer-binary fastapi "uvicorn[standard]" numpy

echo "==> [3/7] Instalando dependencias nodo proyección..."
cd "$PROJ_DIR"
python3 -m venv .venv --system-site-packages
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q --prefer-binary paho-mqtt Pillow

echo "==> [4/7] Preparando assets..."
mkdir -p "$PIXARTEK_DIR/assets/artwork"
sudo usermod -aG video pi

echo "==> [5/7] Habilitando cámara..."
if ! grep -q "^camera_auto_detect=1" /boot/config.txt 2>/dev/null; then
  echo "camera_auto_detect=1" | sudo tee -a /boot/config.txt
fi

echo "==> [6/7] Instalando servicios systemd..."
sudo cp "$PIXARTEK_DIR/deploy/rpi4-b/pixartek-vision.service"     /etc/systemd/system/
sudo cp "$PIXARTEK_DIR/deploy/rpi4-b/pixartek-projection.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pixartek-vision
sudo systemctl enable pixartek-projection

echo "==> [7/7] Iniciando servicios..."
sudo systemctl restart pixartek-vision
sudo systemctl restart pixartek-projection

echo ""
echo "✓ RPi4-B setup completo."
echo "  Stream de video:  http://$(hostname -I | awk '{print $1}'):8000/video_feed"
echo "  Foto fija:        http://$(hostname -I | awk '{print $1}'):8000/capture"
echo "  Estado:           http://$(hostname -I | awk '{print $1}'):8000/status"
echo "  Logs visión:      sudo journalctl -u pixartek-vision -f"
echo "  Logs proyección:  sudo journalctl -u pixartek-projection -f"
