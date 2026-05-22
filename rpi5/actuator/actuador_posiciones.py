#!/usr/bin/env python3
"""
PIXARTEK — Actuador con paradas en posiciones exactas + bombas
En cada parada: motor para, todas las bombas ON 5s, bombas OFF, motor continua.
Posiciones (pasos absolutos desde LIMIT_MIN):
  #0:       0 pasos  — LIMIT_MIN (inicio)
  #1:  64,513 pasos
  #2: 127,679 pasos
  #3: 195,107 pasos
  #4: 265,477 pasos
  Luego continua hasta LIMIT_MAX y para.
"""
import time
import signal
import sys
import lgpio

# ── Actuador pins ─────────────────────────────────────────────────────────────
STEP_PIN  = 2
DIR_PIN   = 3
EN_PIN    = 4
LIMIT_MAX = 6

DERECHA   = 1
GPIO_CHIP = 4
DELAY     = 0.000005

# ── Bomba pins (IN1=HIGH IN2=LOW = forward) ───────────────────────────────────
BOMBAS = [
    {"name": "Bomba #1 Azul",     "in1": 10, "in2": 9},
    {"name": "Bomba #2 Amarilla", "in1": 11, "in2": 25},
    {"name": "Bomba #3 Blanca",   "in1": 14, "in2": 15},
    {"name": "Bomba #4 Negra",    "in1": 18, "in2": 23},
    {"name": "Bomba #5 Roja",     "in1": 17, "in2": 27},
]

PAUSA_SEGUNDOS  = 5   # pause duration at each stop
BOMBAS_SEGUNDOS = 5   # how long pumps run at each stop

POSICIONES = [64_513, 127_679, 195_107, 265_477]


class Actuador:
    def __init__(self):
        self.chip = lgpio.gpiochip_open(GPIO_CHIP)

        # Actuador outputs
        lgpio.gpio_claim_output(self.chip, STEP_PIN, 0)
        lgpio.gpio_claim_output(self.chip, DIR_PIN,  DERECHA)
        lgpio.gpio_claim_output(self.chip, EN_PIN,   1)

        # Limit switch
        lgpio.gpio_claim_input(self.chip, LIMIT_MAX, lgpio.SET_PULL_UP)

        # Bomba outputs — all OFF at start
        for b in BOMBAS:
            lgpio.gpio_claim_output(self.chip, b["in1"], 0)
            lgpio.gpio_claim_output(self.chip, b["in2"], 0)

        signal.signal(signal.SIGINT,  self._salir)
        signal.signal(signal.SIGTERM, self._salir)

    # ── Limit ─────────────────────────────────────────────────────────────────

    def _max_activo(self):
        return lgpio.gpio_read(self.chip, LIMIT_MAX) == 0

    # ── Motor ─────────────────────────────────────────────────────────────────

    def _motor_on(self):
        lgpio.gpio_write(self.chip, EN_PIN, 0)
        time.sleep(0.005)

    def _motor_off(self):
        lgpio.gpio_write(self.chip, EN_PIN, 1)

    def _paso(self):
        lgpio.gpio_write(self.chip, STEP_PIN, 1)
        time.sleep(DELAY)
        lgpio.gpio_write(self.chip, STEP_PIN, 0)
        time.sleep(DELAY)

    # ── Bombas ────────────────────────────────────────────────────────────────

    def _bombas_on(self):
        for b in BOMBAS:
            lgpio.gpio_write(self.chip, b["in1"], 1)
            lgpio.gpio_write(self.chip, b["in2"], 0)
        print(f"  Bombas ON ({BOMBAS_SEGUNDOS}s)...")

    def _bombas_off(self):
        for b in BOMBAS:
            lgpio.gpio_write(self.chip, b["in1"], 0)
            lgpio.gpio_write(self.chip, b["in2"], 0)
        print("  Bombas OFF")

    # ── Stop routine ──────────────────────────────────────────────────────────

    def _hacer_parada(self, label):
        self._motor_off()
        print(f"\n  PARADA en {label}")
        self._bombas_on()
        time.sleep(BOMBAS_SEGUNDOS)
        self._bombas_off()
        time.sleep(0.5)
        self._motor_on()

    # ── Main cycle ────────────────────────────────────────────────────────────

    def correr(self):
        print("=" * 50)
        print("  PIXARTEK — Ciclo con posiciones + bombas")
        print(f"  Paradas en: {POSICIONES}")
        print("=" * 50)

        # Position 0: LIMIT_MIN — pause first
        print("\nPOSICION #0 — LIMIT_MIN (inicio)")
        self._hacer_parada("LIMIT_MIN")

        pasos   = 0
        pos_idx = 0

        print("\nMoviendo hacia LIMIT_MAX...\n")

        while True:
            if self._max_activo():
                self._motor_off()
                self._bombas_off()
                print(f"\nLIMIT_MAX alcanzado en {pasos:,} pasos — STOP")
                break

            self._paso()
            pasos += 1

            if pos_idx < len(POSICIONES) and pasos >= POSICIONES[pos_idx]:
                print(f"POSICION #{pos_idx + 1} — {pasos:,} pasos")
                self._hacer_parada(f"posicion #{pos_idx + 1}")
                pos_idx += 1

        print("\nCiclo completo OK")
        self._limpiar()

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def _salir(self, *_):
        self._bombas_off()
        self._limpiar()
        sys.exit(0)

    def _limpiar(self):
        self._motor_off()
        self._bombas_off()
        lgpio.gpiochip_close(self.chip)


if __name__ == "__main__":
    Actuador().correr()
