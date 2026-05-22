#!/usr/bin/env python3
"""
PIXARTEK — Medidor de posiciones del actuador
El motor se mueve continuamente hacia LIMIT_MAX.
Presiona TAB (o cualquier tecla) para guardar la posicion actual.
Presiona Ctrl+C para terminar y ver todas las posiciones guardadas.
"""
import time
import signal
import sys
import select
import tty
import termios
import lgpio

STEP_PIN  = 2
DIR_PIN   = 3
EN_PIN    = 4
LIMIT_MAX = 6

DERECHA  = 1
GPIO_CHIP = 4

# Delay entre pasos — ajustar si el motor pierde fuerza
DELAY = 0.000005


class Medidor:
    def __init__(self):
        self.chip = lgpio.gpiochip_open(GPIO_CHIP)
        lgpio.gpio_claim_output(self.chip, STEP_PIN, 0)
        lgpio.gpio_claim_output(self.chip, DIR_PIN,  DERECHA)
        lgpio.gpio_claim_output(self.chip, EN_PIN,   1)
        lgpio.gpio_claim_input(self.chip,  LIMIT_MAX, lgpio.SET_PULL_UP)
        self.posiciones = []
        signal.signal(signal.SIGINT, self._salir)

    def _max_activo(self):
        return lgpio.gpio_read(self.chip, LIMIT_MAX) == 0

    def _paso(self):
        lgpio.gpio_write(self.chip, STEP_PIN, 1)
        time.sleep(DELAY)
        lgpio.gpio_write(self.chip, STEP_PIN, 0)
        time.sleep(DELAY)

    def _tecla_presionada(self):
        return select.select([sys.stdin], [], [], 0)[0] != []

    def correr(self):
        print("=" * 50)
        print("  PIXARTEK — Medidor de posiciones")
        print("  Motor moviendose hacia LIMIT_MAX...")
        print("  Presiona cualquier tecla para guardar posicion")
        print("  Ctrl+C para terminar")
        print("=" * 50)

        # Set terminal to raw mode so keypresses register instantly
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setraw(fd)

        lgpio.gpio_write(self.chip, EN_PIN, 0)  # enable motor
        pasos = 0

        try:
            while not self._max_activo():
                self._paso()
                pasos += 1

                if self._tecla_presionada():
                    sys.stdin.read(1)  # consume the keypress
                    num = len(self.posiciones) + 1
                    self.posiciones.append(pasos)
                    # Restore terminal briefly to print
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                    print(f"\n  >>> POSICION #{num} guardada: {pasos:,} pasos")
                    tty.setraw(fd)

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        lgpio.gpio_write(self.chip, EN_PIN, 1)
        print(f"\nLIMIT_MAX alcanzado en {pasos:,} pasos")
        self._mostrar_resumen()
        self._limpiar()

    def _mostrar_resumen(self):
        print("\n" + "=" * 50)
        print("  POSICIONES GUARDADAS:")
        for i, p in enumerate(self.posiciones, 1):
            print(f"  #{i}: {p:,} pasos")
        print("=" * 50)

    def _salir(self, *_):
        print(f"\n\nDetenido.")
        self._mostrar_resumen()
        self._limpiar()
        sys.exit(0)

    def _limpiar(self):
        lgpio.gpio_write(self.chip, EN_PIN, 1)
        lgpio.gpiochip_close(self.chip)


if __name__ == "__main__":
    Medidor().correr()
