#!/usr/bin/env python3
"""
PIXARTEK — Color: Dark Navy (~#0f2130)
"""
import time
import lgpio

GPIO_CHIP         = 4
BASE_SECONDS      = 12

BOMBAS = [
    {"name": "Azul",     "in1": 10, "in2": 9,  "pct": 0.90},
    {"name": "Amarilla", "in1": 25, "in2": 11, "pct": 0.00},
    {"name": "Blanca",   "in1": 14, "in2": 15, "pct": 0.00},
    {"name": "Negra",    "in1": 27, "in2": 17, "pct": 0.10},
    {"name": "Roja",     "in1": 23, "in2": 18, "pct": 0.00},
]


def dispensar(base_seconds=BASE_SECONDS):
    chip = lgpio.gpiochip_open(GPIO_CHIP)
    for b in BOMBAS:
        lgpio.gpio_claim_output(chip, b["in1"], 0)
        lgpio.gpio_claim_output(chip, b["in2"], 0)

    start = time.time()
    stop_times = {b["name"]: start + b["pct"] * base_seconds for b in BOMBAS if b["pct"] > 0}

    print(f"DARK NAVY — dosis {base_seconds}s")
    for b in BOMBAS:
        if b["pct"] > 0:
            print(f"  {b['name']:10s} {int(b['pct']*100)}%  →  {b['pct']*base_seconds:.1f}s")

    for b in BOMBAS:
        if b["pct"] > 0:
            lgpio.gpio_write(chip, b["in1"], 1)
            lgpio.gpio_write(chip, b["in2"], 0)

    print("\nBombas ON...")
    active = {b["name"] for b in BOMBAS if b["pct"] > 0}

    while active:
        now = time.time()
        for b in BOMBAS:
            if b["name"] in active and now >= stop_times[b["name"]]:
                lgpio.gpio_write(chip, b["in1"], 0)
                lgpio.gpio_write(chip, b["in2"], 0)
                active.remove(b["name"])
                print(f"  {b['name']} OFF ({now - start:.1f}s)")
        time.sleep(0.01)

    print("Dispense completo OK")
    lgpio.gpiochip_close(chip)


if __name__ == "__main__":
    dispensar()
