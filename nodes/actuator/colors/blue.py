#!/usr/bin/env python3
"""
PIXARTEK — Color: Blue
Solo Bomba #1 Azul (GPIO 10/9)
"""
import time
import lgpio

GPIO_CHIP         = 4
BASE_SECONDS      = 12

BOMBA_IN1 = 10
BOMBA_IN2 = 9


def dispensar(base_seconds=BASE_SECONDS):
    chip = lgpio.gpiochip_open(GPIO_CHIP)
    lgpio.gpio_claim_output(chip, BOMBA_IN1, 0)
    lgpio.gpio_claim_output(chip, BOMBA_IN2, 0)

    print(f"BLUE — Azul ON por {base_seconds:.2f}s")
    lgpio.gpio_write(chip, BOMBA_IN1, 1)
    lgpio.gpio_write(chip, BOMBA_IN2, 0)
    time.sleep(base_seconds)
    lgpio.gpio_write(chip, BOMBA_IN1, 0)
    lgpio.gpio_write(chip, BOMBA_IN2, 0)

    print("Dispense completo OK")
    lgpio.gpiochip_close(chip)


if __name__ == "__main__":
    dispensar()
