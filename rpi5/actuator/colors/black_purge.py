#!/usr/bin/env python3
"""
PIXARTEK — Black pump purge cycle
  3s forward → 3s backward → 3s forward
"""
import time
import lgpio

GPIO_CHIP = 4
IN1 = 27
IN2 = 17

chip = lgpio.gpiochip_open(GPIO_CHIP)
lgpio.gpio_claim_output(chip, IN1, 0)
lgpio.gpio_claim_output(chip, IN2, 0)

print("Negra — adelante 3s")
lgpio.gpio_write(chip, IN1, 1)
lgpio.gpio_write(chip, IN2, 0)
time.sleep(3)

print("Negra — atras 3s")
lgpio.gpio_write(chip, IN1, 0)
lgpio.gpio_write(chip, IN2, 1)
time.sleep(3)

print("Negra — adelante 3s")
lgpio.gpio_write(chip, IN1, 1)
lgpio.gpio_write(chip, IN2, 0)
time.sleep(3)

lgpio.gpio_write(chip, IN1, 0)
lgpio.gpio_write(chip, IN2, 0)
lgpio.gpiochip_close(chip)
print("Ciclo completo OK")
