#!/usr/bin/env python3
import lgpio, time, sys

STEP_PIN=2; DIR_PIN=3; EN_PIN=4; LIMIT_MAX=6
FRECUENCIA_HZ=50000; DELAY=1.0/FRECUENCIA_HZ/2.0
DERECHA=1; MAX_STEPS=2_000_000; GPIO_CHIP=4

chip = lgpio.gpiochip_open(GPIO_CHIP)
lgpio.gpio_claim_output(chip, STEP_PIN, 0)
lgpio.gpio_claim_output(chip, DIR_PIN,  0)
lgpio.gpio_claim_output(chip, EN_PIN,   1)
lgpio.gpio_claim_input(chip,  LIMIT_MAX, lgpio.SET_PULL_UP)

def at_max():
    return lgpio.gpio_read(chip, LIMIT_MAX) == 0

if at_max():
    print("Actuator already at LIMIT_MAX — OK")
    lgpio.gpiochip_close(chip); sys.exit(0)

print("Moving to LIMIT_MAX...")
lgpio.gpio_write(chip, DIR_PIN, DERECHA)
time.sleep(0.01)
lgpio.gpio_write(chip, EN_PIN, 0)
time.sleep(0.005)

steps = 0
while not at_max():
    lgpio.gpio_write(chip, STEP_PIN, 1); time.sleep(DELAY)
    lgpio.gpio_write(chip, STEP_PIN, 0); time.sleep(DELAY)
    steps += 1
    if steps >= MAX_STEPS:
        print("ERROR: LIMIT_MAX not reached", file=sys.stderr)
        lgpio.gpio_write(chip, EN_PIN, 1)
        lgpio.gpiochip_close(chip); sys.exit(1)

lgpio.gpio_write(chip, EN_PIN, 1)
lgpio.gpiochip_close(chip)
print(f"LIMIT_MAX reached ({steps:,} steps)")
