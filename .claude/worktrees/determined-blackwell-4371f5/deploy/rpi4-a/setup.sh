#!/usr/bin/env bash
# ============================================================
#  PIXARTEK — Setup RPi4-A (Nodo Proyección)
#  Ejecutar en la RPi4-A como usuario pi:
#    bash /tmp/setup.sh
# ============================================================
set -euo pipefail
PIXARTEK_DIR="/home/pi/pixartek"
NODE_DIR="$PIXARTEK_DIR/nodes/projection"

echo "==> [1/5] Actualizando sistema..."
sudo apt-get update -q
sudo apt-get install -y -q \
  python3.11 python3.11-venv \
  feh \
  unclutter \
  xorg \
  curl

echo "==> [2/5] Instalando dependencias Python..."
cd "$NODE_DIR"
python3.11 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q paho-mqtt Pillow

echo "==> [3/5] Deshabilitando screensaver / DPMS / HDMI blanking..."

# X11: deshabilitar DPMS y screensaver
sudo mkdir -p /etc/X11/xorg.conf.d
sudo tee /etc/X11/xorg.conf.d/10-disable-screensaver.conf > /dev/null <<'EOF'
Section "ServerFlags"
  Option "BlankTime"   "0"
  Option "StandbyTime" "0"
  Option "SuspendTime" "0"
  Option "OffTime"     "0"
  Option "NoPM"        "true"
EndSection

Section "Monitor"
  Identifier "Monitor0"
  Option     "DPMS" "false"
EndSection
EOF

# RPi firmware: forzar HDMI siempre encendido (evita que el proyector
# interprete señal estática como "sin fuente")
sudo tee -a /boot/firmware/config.txt > /dev/null <<'EOF'

# PIXARTEK — mantener señal HDMI activa permanentemente
hdmi_force_hotplug=1
hdmi_drive=2
disable_overscan=1
EOF

# Consola Linux: deshabilitar blanking del framebuffer
sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet consoleblank=0"/' \
  /etc/default/grub 2>/dev/null || true

# Añadir xset al perfil de pi para cuando inicia sesión gráfica
grep -q "xset -dpms" /home/pi/.profile 2>/dev/null || cat >> /home/pi/.profile <<'EOF'

# PIXARTEK — prevent display blanking
xset -dpms 2>/dev/null || true
xset s off  2>/dev/null || true
xset s noblank 2>/dev/null || true
EOF

echo "==> [4/5] Instalando servicio systemd..."
sudo cp "$PIXARTEK_DIR/deploy/rpi4-a/pixartek-projection.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pixartek-projection

echo "==> [5/5] Iniciando servicio..."
sudo systemctl start pixartek-projection

echo ""
echo "✓ RPi4-A (Proyección) setup completo."
echo "  Estado: sudo systemctl status pixartek-projection"
echo "  Logs:   sudo journalctl -u pixartek-projection -f"
