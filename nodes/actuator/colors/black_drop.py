#!/usr/bin/env python3
"""
PIXARTEK — Black micro drop: 0.010s forward, 5s wait, suck-back
"""
import time
import lgpio

GPIO_CHIP         = 4
SUCK_BACK_SECONDS = 0.3
IN1               = 27
IN2               = 17

chip = lgpio.gpiochip_open(GPIO_CHIP)
lgpio.gpio_claim_output(chip, IN1, 0)
lgpio.gpio_claim_output(chip, IN2, 0)

print("Negra — adelante 0.010s")
lgpio.gpio_write(chip, IN1, 1)
lgpio.gpio_write(chip, IN2, 0)
time.sleep(0.02 * 12)
lgpio.gpio_write(chip, IN1, 0)
lgpio.gpio_write(chip, IN2, 0)

lgpio.gpiochip_close(chip)
print("OK")
