# test_parallel_ports.py
# Envoie un trigger sur le port 0x3FE8 toutes les secondes pendant 10 secondes.
# Le signal TTL n'est envoyé QUE sur le 1er trigger.
# inpoutx64.dll doit être dans le même dossier que ce script.

import os
import time
import ctypes

# ── Config ────────────────────────────────────────────────────────────────────
PORT         = 0x3FE8
TRIGGER_BYTE = 0xFF   # bit 0 uniquement actif (00000001)
RESET_BYTE   = 0x00   # remet tout à 0
PULSE_S      = 0.050  # durée du pulse (50 ms)
DURATION_S   = 60     # durée totale
INTERVAL_S   = 1.0    # intervalle entre triggers

# ── Chargement de la DLL ──────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
driver = ctypes.WinDLL(os.path.join(SCRIPT_DIR, "inpoutx64.dll"))


# ── Programme principal ───────────────────────────────────────────────────────
def main():
    print(f"Port : 0x{PORT:04X}  |  {DURATION_S} secondes  |  signal TTL toutes les secondes")
    print("=" * 55)

    t0 = time.perf_counter()
    trigger_count = 0
    next_trigger  = t0

    while (time.perf_counter() - t0) < DURATION_S:
        now = time.perf_counter()

        if now >= next_trigger:
            trigger_count += 1
            elapsed = now - t0

            driver.Out32(PORT, TRIGGER_BYTE)
            time.sleep(PULSE_S)
            driver.Out32(PORT, RESET_BYTE)
            print(f"  Trigger {trigger_count:2d}  →  t = {elapsed:.3f} s  [signal TTL envoyé]")

            next_trigger += INTERVAL_S

        time.sleep(0.001)

    driver.Out32(PORT, RESET_BYTE)

    print("=" * 55)
    print(f"Terminé : {trigger_count} triggers, signal TTL envoyé à chaque trigger.")


if __name__ == "__main__":
    main()
