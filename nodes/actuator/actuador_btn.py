#!/usr/bin/env python3
"""
PIXARTEK — Actuador controlado por LIMIT_MIN (GPIO 5)
El motor SOLO se mueve mientras LIMIT_MIN esté siendo presionado.
Al soltar el botón el motor se detiene inmediatamente.
Pins: STEP=2, DIR=3, EN=4, LIMIT_MIN=5
"""
import time
import signal
import sys
import lgpio

STEP_PIN  = 2
DIR_PIN   = 3
EN_PIN    = 4
LIMIT_MIN = 5

FRECUENCIA_HZ = 50000
DELAY         = 1.0 / FRECUENCIA_HZ / 2.0
DERECHA       = 1

GPIO_CHIP = 4   # RPi5 uses gpiochip4


class Actuador:
    def __init__(self):
        self.chip = lgpio.gpiochip_open(GPIO_CHIP)
        lgpio.gpio_claim_output(self.chip, STEP_PIN, 0)
        lgpio.gpio_claim_output(self.chip, DIR_PIN,  DERECHA)
        lgpio.gpio_claim_output(self.chip, EN_PIN,   1)  # HIGH = disabled
        lgpio.gpio_claim_input(self.chip,  LIMIT_MIN, lgpio.SET_PULL_UP)
        signal.signal(signal.SIGINT,  self._salir)
        signal.signal(signal.SIGTERM, self._salir)

    def _btn_presionado(self):
        return lgpio.gpio_read(self.chip, LIMIT_MIN) == 0  # LOW = pressed

    def correr(self):
        print("PIXARTEK actuador: esperando LIMIT_MIN...")
        print("Manten presionado LIMIT_MIN para mover el actuador.")

        motor_on = False

        while True:
            if self._btn_presionado():
                if not motor_on:
                    lgpio.gpio_write(self.chip, EN_PIN, 0)   # enable motor
                    motor_on = True
                    print("LIMIT_MIN presionado — motor ON")
                # Step while button is held
                lgpio.gpio_write(self.chip, STEP_PIN, 1)
                time.sleep(DELAY)
                lgpio.gpio_write(self.chip, STEP_PIN, 0)
                time.sleep(DELAY)
            else:
                if motor_on:
                    lgpio.gpio_write(self.chip, EN_PIN, 1)   # disable motor
                    motor_on = False
                    print("LIMIT_MIN suelto — motor OFF")
                time.sleep(0.01)   # idle poll

    def _salir(self, *_):
        lgpio.gpio_write(self.chip, EN_PIN, 1)  # disable motor
        lgpio.gpiochip_close(self.chip)
        print("GPIO liberado.")
        sys.exit(0)


if __name__ == "__main__":
    Actuador().correr()
