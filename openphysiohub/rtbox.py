"""
rtbox.py
────────
RTBox button-box serial communication.

Data flow
─────────
  button press  →  RTBox sends 7 bytes over USB serial
  serial thread reads code  →  sends TTL back to RTBox DB-25 TTL OUT
  RTBox forwards TTL  →  BIOPAC digital input
  event stored in thread-safe queue  →  consumed by Stroop loop

Public API
──────────
    rtbox_open()            start the background serial thread
    rtbox_close()           stop the thread cleanly
    rtbox_pop_events()      return and flush accumulated button events
"""

import time
import threading
import serial

from .config import (
    RTBOX_PORT,
    RTBOX_BAUD,
    RTBOX_CLOCK_HZ,
    RTBOX_ENABLE,
    RTBOX_EVENT_MAP,
)

# ── Thread-shared state ──────────────────────────────────────────────────────
_ser:       serial.Serial | None = None
_events:    list[dict]           = []
_lock       = threading.Lock()
_stop_ev    = threading.Event()


# ═══════════════════════════════════════════════════════════════════════════════
#  Internal helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _bytes2secs(b7: bytes) -> float:
    """Convert the 6-byte RTBox timestamp to seconds (clock = RTBOX_CLOCK_HZ)."""
    ticks = int.from_bytes(b7[1:7], byteorder="big")
    return ticks / RTBOX_CLOCK_HZ


def _send_ttl(ser: serial.Serial, value: int) -> None:
    """Send an 8-bit event code to the RTBox DB-25 TTL OUT (pins 1-8)."""
    ser.write(bytes([1, value & 0xFF]))


def _serial_loop(stop_event: threading.Event) -> None:
    """Background thread: read button events, forward TTL, store for Stroop."""
    global _ser

    try:
        ser = serial.Serial(RTBOX_PORT, RTBOX_BAUD, timeout=0.1)
        _ser = ser
        print(f"[RTBox] Port ouvert : {RTBOX_PORT} @ {RTBOX_BAUD} baud")
    except Exception as e:
        print(f"[RTBox] AVERTISSEMENT — impossible d'ouvrir {RTBOX_PORT} : {e}")
        _ser = None
        return

    # Firmware init: advanced mode + enable press events
    ser.reset_input_buffer()
    ser.write(b"X")                           # enter advanced mode
    time.sleep(0.3)
    ser.read(ser.in_waiting)                  # flush ID response
    ser.write(bytes([101, RTBOX_ENABLE]))     # enable press (bit 0)
    time.sleep(0.2)
    ser.reset_input_buffer()
    print(f"[RTBox] Prêt — events press activés (mask={RTBOX_ENABLE:#010b})")
    print(f"[RTBox] TTL codes : Btn1→1  Btn2→2  Btn3→4  Btn4→8")

    leftover = b""
    while not stop_event.is_set():
        try:
            waiting = ser.in_waiting
            chunk   = ser.read(max(waiting, 1)) if waiting else b""
            if not chunk:
                time.sleep(0.005)
                continue

            data     = leftover + chunk
            leftover = b""
            i = 0
            while i <= len(data) - 7:
                raw7     = data[i : i + 7]
                code     = raw7[0]
                box_secs = _bytes2secs(raw7)

                if code in RTBOX_EVENT_MAP:
                    btn_name, ttl_val = RTBOX_EVENT_MAP[code]
                    host_t = time.perf_counter()

                    _send_ttl(ser, ttl_val)
                    print(f"  [RTBox] {btn_name}  box={box_secs:.4f}s  TTL→{ttl_val}")

                    with _lock:
                        _events.append({
                            "btn":      btn_name,
                            "host_t":   host_t,
                            "box_secs": box_secs,
                            "ttl":      ttl_val,
                        })

                    # Firmware v5.0 disables light detection after each light
                    # event — re-enable immediately
                    if btn_name == "light":
                        time.sleep(0.2)
                        ser.write(bytes([101, RTBOX_ENABLE]))
                        ser.read(1)   # consume ack byte (0x65)

                elif code != 0x65:   # 0x65 = silent ack 'e', ignore
                    print(f"  [RTBox] code inconnu : 0x{code:02X}")

                i += 7

            if i < len(data):
                leftover = data[i:]

        except Exception as e:
            print(f"[RTBox] Erreur série : {e}")
            time.sleep(0.1)

    # Clean shutdown
    try:
        _send_ttl(ser, 0)  # drive TTL low
        ser.write(b"x")    # return to simple mode
        ser.close()
        print("[RTBox] Port fermé.")
    except Exception:
        pass

    _ser = None


# ═══════════════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════════════

def rtbox_open() -> None:
    """Start the background serial thread."""
    _stop_ev.clear()
    t = threading.Thread(target=_serial_loop, args=(_stop_ev,), daemon=True)
    t.start()
    time.sleep(0.8)   # allow firmware init to complete


def rtbox_close() -> None:
    """Signal the serial thread to stop and wait briefly for clean shutdown."""
    _stop_ev.set()
    time.sleep(0.4)


def rtbox_pop_events() -> list[dict]:
    """Return and flush all accumulated button events (thread-safe)."""
    with _lock:
        evts = list(_events)
        _events.clear()
    return evts
