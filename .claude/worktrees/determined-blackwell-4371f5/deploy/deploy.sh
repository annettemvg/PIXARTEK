#!/usr/bin/env bash
# ============================================================
#  PIXARTEK — Deploy maestro (corre desde tu Mac)
#
#  Uso:
#    ./deploy/deploy.sh [all | rpi5 | rpi4a | rpi4b]
#
#  Pre-requisitos:
#    - SSH key configurada para pi@<IP>
#    - Las IPs en la sección CONFIG coinciden con tu red
# ============================================================
set -euo pipefail

# ── CONFIG ───────────────────────────────────────────────────
# Valores por defecto — sobreescribe en deploy/.env si tienes IPs distintas
RPI5_IP="192.168.1.10"
RPI4A_IP="192.168.1.11"
RPI4B_IP="192.168.1.12"
SSH_USER="pi"
REMOTE_DIR="/home/pi/pixartek"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Carga overrides locales si existe deploy/.env
ENV_FILE="$(dirname "$0")/.env"
# shellcheck disable=SC1090
[[ -f "$ENV_FILE" ]] && source "$ENV_FILE"
# ─────────────────────────────────────────────────────────────

TARGET="${1:-all}"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5"

# Color output
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[deploy]${NC} $*"; }
warn()  { echo -e "${YELLOW}[deploy]${NC} $*"; }
error() { echo -e "${RED}[deploy]${NC} $*"; exit 1; }

check_ssh() {
  local ip=$1 name=$2
  if ! ssh $SSH_OPTS "${SSH_USER}@${ip}" "echo ok" &>/dev/null; then
    error "No se puede conectar a $name ($ip) — verifica SSH y la IP"
  fi
  info "SSH OK → $name ($ip)"
}

rsync_node() {
  local ip=$1 name=$2
  info "Sincronizando código → $name ($ip)..."
  rsync -az --delete \
    --exclude '.git' \
    --exclude '.next' \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.venv' \
    --exclude '*.db' \
    -e "ssh $SSH_OPTS" \
    "${LOCAL_DIR}/" "${SSH_USER}@${ip}:${REMOTE_DIR}/"
  info "Rsync completo → $name"
}

run_setup() {
  local ip=$1 name=$2 script=$3
  info "Ejecutando setup en $name..."
  ssh $SSH_OPTS "${SSH_USER}@${ip}" "bash ${REMOTE_DIR}/${script}" \
    || error "Setup falló en $name"
  info "Setup completo → $name"
}

# ── DEPLOY RPi5 ──────────────────────────────────────────────
deploy_rpi5() {
  info "=== Desplegando RPi5 (Principal) ==="
  check_ssh "$RPI5_IP" "RPi5"
  rsync_node "$RPI5_IP" "RPi5"
  run_setup  "$RPI5_IP" "RPi5" "deploy/rpi5/setup.sh"
}

# ── DEPLOY RPi4-A ────────────────────────────────────────────
deploy_rpi4a() {
  info "=== Desplegando RPi4-A (Proyección) ==="
  check_ssh "$RPI4A_IP" "RPi4-A"
  rsync_node "$RPI4A_IP" "RPi4-A"
  run_setup  "$RPI4A_IP" "RPi4-A" "deploy/rpi4-a/setup.sh"
}

# ── DEPLOY RPi4-B ────────────────────────────────────────────
deploy_rpi4b() {
  info "=== Desplegando RPi4-B (Visión) ==="
  check_ssh "$RPI4B_IP" "RPi4-B"
  rsync_node "$RPI4B_IP" "RPi4-B"
  run_setup  "$RPI4B_IP" "RPi4-B" "deploy/rpi4-b/setup.sh"
}

# ── STATUS ───────────────────────────────────────────────────
status_all() {
  info "=== Estado de servicios ==="
  for ip_name in "$RPI5_IP:RPi5" "$RPI4A_IP:RPi4-A" "$RPI4B_IP:RPi4-B"; do
    ip="${ip_name%%:*}"; name="${ip_name##*:}"
    if ssh $SSH_OPTS "${SSH_USER}@${ip}" "echo ok" &>/dev/null; then
      ssh $SSH_OPTS "${SSH_USER}@${ip}" \
        "systemctl is-active pixartek-backend pixartek-frontend pixartek-projection pixartek-vision 2>/dev/null || true"
      info "$name → conectado"
    else
      warn "$name ($ip) → sin respuesta"
    fi
  done
}

# ── MAIN ─────────────────────────────────────────────────────
case "$TARGET" in
  all)
    deploy_rpi5
    deploy_rpi4a
    deploy_rpi4b
    status_all
    ;;
  rpi5)   deploy_rpi5 ;;
  rpi4a)  deploy_rpi4a ;;
  rpi4b)  deploy_rpi4b ;;
  status) status_all ;;
  *)
    echo "Uso: $0 [all | rpi5 | rpi4a | rpi4b | status]"
    exit 1
    ;;
esac

info "Deploy finalizado."
