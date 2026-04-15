"""
trigger.py
──────────
Digital trigger output via inpoutx64.dll (parallel port → BIOPAC).

Public API
──────────
    send_trigger(n=1)   send n TTL pulses on the parallel port
"""

import time
import ctypes

from .config import LIB_BIOPAC_DIR, TRIGGER_PORT, TRIGGER_BYTE, RESET_BYTE, PULSE_S

# ── Parallel port driver ─────────────────────────────────────────────────────
_driver = ctypes.WinDLL(str(LIB_BIOPAC_DIR / "inpoutx64.dll"))


# ═══════════════════════════════════════════════════════════════════════════════

def send_trigger(n: int = 1) -> None:
    """
    Send n TTL pulses via the parallel port to BIOPAC.

    Each pulse is PULSE_S seconds high followed by PULSE_S seconds low.
    Multiple pulses have a PULSE_S gap between them.
    """
    for i in range(n):
        _driver.Out32(TRIGGER_PORT, TRIGGER_BYTE)
        time.sleep(PULSE_S)
        _driver.Out32(TRIGGER_PORT, RESET_BYTE)
        if i < n - 1:
            time.sleep(PULSE_S)


def reset_trigger() -> None:
    """Drive the parallel port low (safe cleanup on exit)."""
    _driver.Out32(TRIGGER_PORT, RESET_BYTE)
