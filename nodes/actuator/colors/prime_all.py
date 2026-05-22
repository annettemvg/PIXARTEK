#!/usr/bin/env python3
"""
PIXARTEK — Prime all pumps (no suck-back)
  Runs each pump forward for BASE_SECONDS to fill tubes to nozzle tip.
"""
import time
import lgpio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pump_state

GPIO_CHIP    = 4
BASE_SECONDS = 3

BOMBAS = [
    {"name": "Roja",     "in1": 23, "in2": 18},
    {"name": "Blanca",   "in1": 14, "in2": 15},
    {"name": "Azul",     "in1": 10, "in2": 9},
    {"name": "Negra",    "in1": 27, "in2": 17},
    {"name": "Amarilla", "in1": 25, "in2": 11},
]

chip = lgpio.gpiochip_open(GPIO_CHIP)
for b in BOMBAS:
    lgpio.gpio_claim_output(chip, b["in1"], 0)
    lgpio.gpio_claim_output(chip, b["in2"], 0)

for b in BOMBAS:
    print(f"{b['name']} — adelante {BASE_SECONDS}s")
    lgpio.gpio_write(chip, b["in1"], 1)
    lgpio.gpio_write(chip, b["in2"], 0)
    time.sleep(BASE_SECONDS)
    lgpio.gpio_write(chip, b["in1"], 0)
    lgpio.gpio_write(chip, b["in2"], 0)
    print(f"{b['name']} — OFF")

lgpio.gpiochip_close(chip)

pump_state.save({p: 0.0 for p in ["Azul", "Amarilla", "Blanca", "Negra", "Roja"]})
print("Pump state reset to zero — tubes are full")
print("Prime completo OK")
