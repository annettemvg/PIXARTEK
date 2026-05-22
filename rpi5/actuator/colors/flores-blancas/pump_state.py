#!/usr/bin/env python3
"""
Tracks last suck-back time per pump so next dispense compensates exactly.
State is saved to pump_state.json in the same folder.
"""
import json
import os

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pump_state.json")

PUMPS = ["Azul", "Amarilla", "Blanca", "Negra", "Roja"]


def load():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {p: 0.0 for p in PUMPS}


def save(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
