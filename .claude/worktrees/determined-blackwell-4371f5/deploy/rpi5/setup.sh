#!/usr/bin/env bash
# ============================================================
#  PIXARTEK — Setup RPi5 (Nodo Principal)
#  Ejecutar en la RPi5 como usuario pi:
#    bash /tmp/setup.sh
# ============================================================
set -euo pipefail
PIXARTEK_DIR="/home/pi/pixartek"
DATA_DIR="$PIXARTEK_DIR/data"

echo "==> [1/7] Actualizando sistema..."
sudo apt-get update -q
sudo apt-get install -y -q \
  python3 python3-venv python3-dev \
  mosquitto mosquitto-clients \
  nodejs npm \
  sqlite3 \
  curl git \
  rustc cargo libssl-dev pkg-config

echo "==> [2/7] Configurando Mosquitto..."
sudo cp "$PIXARTEK_DIR/deploy/mosquitto.conf" /etc/mosquitto/conf.d/pixartek.conf
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto

echo "==> [3/7] Preparando base de datos..."
mkdir -p "$DATA_DIR"
chmod 750 "$DATA_DIR"

echo "==> [4/7] Instalando backend Python..."
cd "$PIXARTEK_DIR/backend"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt greenlet

echo "==> [5/7] Build del frontend Next.js..."
cd "$PIXARTEK_DIR/frontend"
npm ci --silent
# Obtener IP del RPi5 para embeber en el bundle
RPI5_IP=$(hostname -I | awk '{print $1}')
NEXT_PUBLIC_API_URL="http://${RPI5_IP}:8000" \
NEXT_PUBLIC_WS_URL="ws://${RPI5_IP}:8000" \
npm run build
# standalone no copia estos directorios automáticamente
rm -rf .next/standalone/.next/static .next/standalone/public
cp -r .next/static   .next/standalone/.next/static
cp -r public         .next/standalone/public

echo "==> [6/7] Instalando servicios systemd..."
sudo cp "$PIXARTEK_DIR/deploy/rpi5/pixartek-backend.service"  /etc/systemd/system/
sudo cp "$PIXARTEK_DIR/deploy/rpi5/pixartek-frontend.service" /etc/systemd/system/
sudo cp "$PIXARTEK_DIR/deploy/rpi5/pixartek-kiosk.service"    /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pixartek-backend
sudo systemctl enable pixartek-frontend
sudo systemctl enable pixartek-kiosk

echo "==> [7/7] Iniciando servicios..."
sudo systemctl start pixartek-backend
sudo systemctl start pixartek-frontend
sleep 3
sudo systemctl start pixartek-kiosk

echo ""
echo "✓ RPi5 setup completo."
echo "  Backend:  http://localhost:8000/health"
echo "  Frontend: http://localhost:3000"
echo "  MQTT:     localhost:1883"
