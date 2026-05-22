#!/usr/bin/env python3
"""
PIXARTEK — TMC2209 Stepper Actuator (RPi5 / gpiochip4)
One dispense cycle: RIGHT until LIMIT_MAX, LEFT until LIMIT_MIN, stop.
Pins: STEP=2, DIR=3, EN=4, LIMIT_MIN=5, LIMIT_MAX=6
"""
import time
import signal
import sys
import lgpio

STEP_PIN  = 2
DIR_PIN   = 3
EN_PIN    = 4
LIMIT_MIN = 5
LIMIT_MAX = 6

FRECUENCIA_HZ     = 50000
DELAY             = 1.0 / FRECUENCIA_HZ / 2.0
DERECHA           = 1
IZQUIERDA         = 0
MAX_STEPS_PER_LEG = 2_000_000

GPIO_CHIP = 4   # RPi5 uses gpiochip4


class Actuador:
    def __init__(self):
        self.chip = lgpio.gpiochip_open(GPIO_CHIP)

        lgpio.gpio_claim_output(self.chip, STEP_PIN, 0)
        lgpio.gpio_claim_output(self.chip, DIR_PIN,  0)
        lgpio.gpio_claim_output(self.chip, EN_PIN,   1)  # HIGH = disabled
        lgpio.gpio_claim_input(self.chip,  LIMIT_MIN, lgpio.SET_PULL_UP)
        lgpio.gpio_claim_input(self.chip,  LIMIT_MAX, lgpio.SET_PULL_UP)

        signal.signal(signal.SIGINT,  self._salir)
        signal.signal(signal.SIGTERM, self._salir)

    def _min_activo(self):
        return lgpio.gpio_read(self.chip, LIMIT_MIN) == 0  # LOW = pressed

    def _max_activo(self):
        return lgpio.gpio_read(self.chip, LIMIT_MAX) == 0  # LOW = pressed

    def _on(self):
        lgpio.gpio_write(self.chip, EN_PIN, 0)  # LOW = enabled
        time.sleep(0.005)

    def _off(self):
        lgpio.gpio_write(self.chip, EN_PIN, 1)  # HIGH = disabled

    def _set_dir(self, d):
        lgpio.gpio_write(self.chip, DIR_PIN, d)
        time.sleep(0.01)

    def _paso(self):
        lgpio.gpio_write(self.chip, STEP_PIN, 1)
        time.sleep(DELAY)
        lgpio.gpio_write(self.chip, STEP_PIN, 0)
        time.sleep(DELAY)

    def dispensar(self):
        print("PIXARTEK actuador: iniciando ciclo de dispense")
        self._on()

        # Leg 1: RIGHT → LIMIT_MAX
        self._set_dir(DERECHA)
        pasos = 0
        while not self._max_activo():
            self._paso()
            pasos += 1
            if pasos >= MAX_STEPS_PER_LEG:
                print("ABORT: LIMIT_MAX no alcanzado", file=sys.stderr)
                self._limpiar()
                sys.exit(1)
        print(f"LIMIT_MAX alcanzado ({pasos:,} pasos) — regresando")

        # Leg 2: LEFT → LIMIT_MIN
        self._set_dir(IZQUIERDA)
        pasos = 0
        while not self._min_activo():
            self._paso()
            pasos += 1
            if pasos >= MAX_STEPS_PER_LEG:
                print("ABORT: LIMIT_MIN no alcanzado", file=sys.stderr)
                self._limpiar()
                sys.exit(1)
        print(f"LIMIT_MIN alcanzado ({pasos:,} pasos) — ciclo completo")

        self._limpiar()
        print("PIXARTEK actuador: ciclo completo OK")

    def _salir(self, *_):
        self._limpiar()
        sys.exit(0)

    def _limpiar(self):
        self._off()
        lgpio.gpiochip_close(self.chip)


if __name__ == "__main__":
    Actuador().dispensar()
