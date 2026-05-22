#!/usr/bin/env python3
"""
PIXARTEK — Color: White
Solo Bomba #3 Blanca (GPIO 14/15)
"""
import time
import lgpio

GPIO_CHIP         = 4
BASE_SECONDS      = 12

BOMBA_IN1 = 14
BOMBA_IN2 = 15


def dispensar(base_seconds=BASE_SECONDS):
    chip = lgpio.gpiochip_open(GPIO_CHIP)
    lgpio.gpio_claim_output(chip, BOMBA_IN1, 0)
    lgpio.gpio_claim_output(chip, BOMBA_IN2, 0)

    print(f"WHITE — Blanca ON por {base_seconds:.2f}s")
    lgpio.gpio_write(chip, BOMBA_IN1, 1)
    lgpio.gpio_write(chip, BOMBA_IN2, 0)
    time.sleep(base_seconds)
    lgpio.gpio_write(chip, BOMBA_IN1, 0)
    lgpio.gpio_write(chip, BOMBA_IN2, 0)

    print("Dispense completo OK")
    lgpio.gpiochip_close(chip)


if __name__ == "__main__":
    dispensar()
