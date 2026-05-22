#!/usr/bin/env python3
"""
PIXARTEK — Ciclo Faro Nocturno (posiciones guardadas)

HOME (sin mover)       → amarillo_dorado.py
Parada #1:  60,338     → naranja.py
Parada #2: 129,148     → indigo.py
Parada #3: 200,036     → black.py
Luego avanza hasta LIMIT_MAX y para.
"""
import time
import signal
import sys
import subprocess
import os
import lgpio

STEP_PIN  = 2
DIR_PIN   = 3
EN_PIN    = 4
LIMIT_MIN = 5
LIMIT_MAX = 6
DERECHA   = 1
GPIO_CHIP = 4
DELAY     = 0.000005

HERE = os.path.dirname(os.path.abspath(__file__))

# Primer color: se dispensa en HOME sin mover
COLOR_INICIO = os.path.join(HERE, "amarillo_dorado.py")

# Paradas con movimiento
PARADAS = [
    (60_338,  os.path.join(HERE, "naranja.py")),
    (129_148, os.path.join(HERE, "indigo.py")),
    (200_036, os.path.join(HERE, "black.py")),
]

# Bursts: inicio→#1: 60338 | #1→#2: 68810 | #2→#3: 70888
BURSTS = [PARADAS[0][0]] + [
    PARADAS[i][0] - PARADAS[i-1][0] for i in range(1, len(PARADAS))
]


class CicloFaroNocturno:
    def __init__(self):
        self.chip = lgpio.gpiochip_open(GPIO_CHIP)
        lgpio.gpio_claim_output(self.chip, STEP_PIN, 0)
        lgpio.gpio_claim_output(self.chip, DIR_PIN,  0)
        lgpio.gpio_claim_output(self.chip, EN_PIN,   1)
        lgpio.gpio_claim_input(self.chip,  LIMIT_MIN, lgpio.SET_PULL_UP)
        lgpio.gpio_claim_input(self.chip,  LIMIT_MAX, lgpio.SET_PULL_UP)
        signal.signal(signal.SIGINT,  self._salir)
        signal.signal(signal.SIGTERM, self._salir)

    def _max_activo(self):
        return lgpio.gpio_read(self.chip, LIMIT_MAX) == 0

    def _motor_on(self):
        lgpio.gpio_write(self.chip, EN_PIN, 0)
        time.sleep(0.005)

    def _motor_off(self):
        lgpio.gpio_write(self.chip, EN_PIN, 1)

    def _set_dir(self, d):
        lgpio.gpio_write(self.chip, DIR_PIN, d)
        time.sleep(0.01)

    def _paso(self):
        lgpio.gpio_write(self.chip, STEP_PIN, 1)
        time.sleep(DELAY)
        lgpio.gpio_write(self.chip, STEP_PIN, 0)
        time.sleep(DELAY)

    def _mover(self, pasos, label=""):
        print(f"  Moviendo {pasos:,} pasos{' — ' + label if label else ''}...")
        for n in range(pasos):
            if self._max_activo():
                print(f"  ⚠ LIMIT_MAX alcanzado en paso {n:,} — abortando")
                return False
            self._paso()
        return True

    def _dispensar(self, filepath):
        name = os.path.basename(filepath)
        print(f"  🎨 Dispensando {name}...")
        self._motor_off()
        lgpio.gpiochip_close(self.chip)
        subprocess.run(["/usr/bin/python3", filepath], check=True)
        self.chip = lgpio.gpiochip_open(GPIO_CHIP)
        lgpio.gpio_claim_output(self.chip, STEP_PIN, 0)
        lgpio.gpio_claim_output(self.chip, DIR_PIN,  0)
        lgpio.gpio_claim_output(self.chip, EN_PIN,   1)
        lgpio.gpio_claim_input(self.chip,  LIMIT_MIN, lgpio.SET_PULL_UP)
        lgpio.gpio_claim_input(self.chip,  LIMIT_MAX, lgpio.SET_PULL_UP)
        print(f"  ✓ {name} OK")

    def correr(self):
        print("=" * 50)
        print("  CICLO FARO NOCTURNO — posiciones guardadas")
        print("=" * 50)
        print(f"  HOME               → {os.path.basename(COLOR_INICIO)}")
        for i, (pos, script) in enumerate(PARADAS, 1):
            print(f"  Parada #{i}: {pos:,} → {os.path.basename(script)}")
        print("=" * 50)

        # Color #1 en HOME — sin mover
        print("\nCubículo HOME — dispensando primer color")
        self._dispensar(COLOR_INICIO)

        # Mover a cada cubículo y dispensar
        self._motor_on()
        self._set_dir(DERECHA)

        for i, (burst, (pos_abs, filepath)) in enumerate(zip(BURSTS, PARADAS), 2):
            print(f"\nCubículo #{i} — posición: {pos_abs:,} pasos (burst: {burst:,})")
            ok = self._mover(burst, label=f"→ cubículo #{i}")
            if not ok:
                self._limpiar()
                return
            self._dispensar(filepath)
            self._motor_on()
            self._set_dir(DERECHA)

        print("\nTodos los colores dispensados — avanzando hasta LIMIT_MAX...")
        while not self._max_activo():
            self._paso()

        self._motor_off()
        print("✓ LIMIT_MAX alcanzado — ciclo completo OK")
        print("=" * 50)
        self._limpiar()

    def _salir(self, *_):
        print("\nInterrupción — apagando motor")
        self._limpiar()
        sys.exit(0)

    def _limpiar(self):
        self._motor_off()
        lgpio.gpiochip_close(self.chip)


if __name__ == "__main__":
    CicloFaroNocturno().correr()
