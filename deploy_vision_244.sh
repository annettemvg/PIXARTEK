#!/bin/bash
set -euo pipefail

HOST="192.168.86.244"
USER="pi"
PASSWORD="12345678"

echo "=========================================="
echo "Desplegando Vision Node en $HOST"
echo "=========================================="

# Usar expect para manejar la autenticación por contraseña
expect << 'EXPECTEOF'
set timeout 30
set password "12345678"

spawn ssh -o StrictHostKeyChecking=no pi@192.168.86.244

expect "password:"
send "$password\r"
expect "$"

# Crear directorio
send "mkdir -p /home/pi/pixartek && cd /home/pi/pixartek && pwd\r"
expect "$"

send "exit\r"
EXPECTEOF

echo "SSH test complete - now deploying..."

