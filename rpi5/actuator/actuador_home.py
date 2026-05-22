#!/usr/bin/env python3
"""
PIXARTEK — Actuator Home on Boot
Checks if actuator is at LIMIT_MIN. If not, moves left until MIN is reached.
"""
import lgpio
import time
import sys

STEP_PIN  = 2
DIR_PIN   = 3
EN_PIN    = 4
LIMIT_MIN = 5
LIMIT_MAX = 6

FRECUENCIA_HZ     = 50000
DELAY             = 1.0 / FRECUENCIA_HZ / 2.0
IZQUIERDA         = 0
MAX_STEPS         = 2_000_000

GPIO_CHIP = 4

chip = lgpio.gpiochip_open(GPIO_CHIP)

lgpio.gpio_claim_output(chip, STEP_PIN, 0)
lgpio.gpio_claim_output(chip, DIR_PIN,  0)
lgpio.gpio_claim_output(chip, EN_PIN,   1)
lgpio.gpio_claim_input(chip,  LIMIT_MIN, lgpio.SET_PULL_UP)
lgpio.gpio_claim_input(chip,  LIMIT_MAX, lgpio.SET_PULL_UP)

def at_min():
    return lgpio.gpio_read(chip, LIMIT_MIN) == 0

if at_min():
    print("Actuator already at LIMIT_MIN — OK")
    lgpio.gpiochip_close(chip)
    sys.exit(0)

print("Actuator not at MIN — moving to LIMIT_MIN...")
lgpio.gpio_write(chip, DIR_PIN, IZQUIERDA)
time.sleep(0.01)
lgpio.gpio_write(chip, EN_PIN, 0)
time.sleep(0.005)

steps = 0
while not at_min():
    lgpio.gpio_write(chip, STEP_PIN, 1)
    time.sleep(DELAY)
    lgpio.gpio_write(chip, STEP_PIN, 0)
    time.sleep(DELAY)
    steps += 1
    if steps >= MAX_STEPS:
        print("ERROR: LIMIT_MIN not reached after max steps", file=sys.stderr)
        lgpio.gpio_write(chip, EN_PIN, 1)
        lgpio.gpiochip_close(chip)
        sys.exit(1)

lgpio.gpio_write(chip, EN_PIN, 1)
lgpio.gpiochip_close(chip)
print(f"LIMIT_MIN reached ({steps:,} steps) — homed OK")
