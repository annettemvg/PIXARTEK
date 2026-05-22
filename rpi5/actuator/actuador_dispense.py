#!/usr/bin/env python3
"""
PIXARTEK — Ciclo de dispense con pausas
Mueve 63,583 pasos → pausa 5s → mueve 63,583 pasos → pausa 5s → ...
hasta tocar LIMIT_MAX, luego regresa hasta LIMIT_MIN y para.
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

DERECHA       = 1
IZQUIERDA     = 0

PASOS_POR_BURST = 63_583
PAUSA_SEGUNDOS  = 5
GPIO_CHIP       = 4   # RPi5 uses gpiochip4


class Actuador:
    def __init__(self):
        self.chip = lgpio.gpiochip_open(GPIO_CHIP)
        lgpio.gpio_claim_output(self.chip, STEP_PIN, 0)
        lgpio.gpio_claim_output(self.chip, DIR_PIN,  0)
        lgpio.gpio_claim_output(self.chip, EN_PIN,   1)
        lgpio.gpio_claim_input(self.chip,  LIMIT_MIN, lgpio.SET_PULL_UP)
        lgpio.gpio_claim_input(self.chip,  LIMIT_MAX, lgpio.SET_PULL_UP)
        signal.signal(signal.SIGINT,  self._salir)
        signal.signal(signal.SIGTERM, self._salir)

    def _min_activo(self):
        return lgpio.gpio_read(self.chip, LIMIT_MIN) == 0

    def _max_activo(self):
        return lgpio.gpio_read(self.chip, LIMIT_MAX) == 0

    def _on(self):
        lgpio.gpio_write(self.chip, EN_PIN, 0)
        time.sleep(0.005)

    def _off(self):
        lgpio.gpio_write(self.chip, EN_PIN, 1)

    def _set_dir(self, d):
        lgpio.gpio_write(self.chip, DIR_PIN, d)
        time.sleep(0.01)

    def _paso(self):
        lgpio.gpio_write(self.chip, STEP_PIN, 1)
        time.sleep(0.000005)
        lgpio.gpio_write(self.chip, STEP_PIN, 0)
        time.sleep(0.000005)

    def dispensar(self):
        print("PIXARTEK: iniciando ciclo de dispense")
        print(f"Pausa inicial {PAUSA_SEGUNDOS}s en posicion de inicio...")
        time.sleep(PAUSA_SEGUNDOS)
        self._on()
        self._set_dir(DERECHA)

        burst = 0

        # ── Fase 1: bursts hacia LIMIT_MAX ────────────────────────────────────
        while True:
            burst += 1
            print(f"Burst #{burst} — moviendo {PASOS_POR_BURST:,} pasos...")

            for paso in range(PASOS_POR_BURST):
                if self._max_activo():
                    print(f"LIMIT_MAX alcanzado en burst #{burst} paso {paso:,} — regresando")
                    self._regresar()
                    return
                self._paso()

            print(f"Burst #{burst} completo — pausando {PAUSA_SEGUNDOS}s")
            self._off()
            time.sleep(PAUSA_SEGUNDOS)
            self._on()
            self._set_dir(DERECHA)

    def _regresar(self):
        self._set_dir(IZQUIERDA)
        pasos = 0
        while not self._min_activo():
            self._paso()
            pasos += 1
        print(f"LIMIT_MIN alcanzado ({pasos:,} pasos) — ciclo completo OK")
        self._limpiar()

    def _salir(self, *_):
        self._limpiar()
        sys.exit(0)

    def _limpiar(self):
        self._off()
        lgpio.gpiochip_close(self.chip)


if __name__ == "__main__":
    Actuador().dispensar()
