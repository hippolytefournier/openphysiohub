"""
config.py
─────────
All hard-coded constants for the experiment.
No logic, no side-effects — safe to import from any module.
"""

import os
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
#  PATHS
# ═══════════════════════════════════════════════════════════════════════════════

# Project root  =  the directory that contains openphysiohub/
PROJECT_ROOT   = Path(__file__).resolve().parent.parent

LIB_ET_DIR     = PROJECT_ROOT / "eye_tracking_library"
LIB_BIOPAC_DIR = PROJECT_ROOT / "biopac_input_library"
LIB_RTBOX_DIR  = PROJECT_ROOT / "button_box_library"
DATA_DIR       = PROJECT_ROOT / "data"

os.makedirs(DATA_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  BIOPAC
# ═══════════════════════════════════════════════════════════════════════════════

BIOPAC_DLL_PATH = (
    r"C:\Program Files (x86)\BIOPAC Systems, Inc"
    r"\BIOPAC Hardware API 2.2 Research\x64\mpdev.dll"
)

DEVNAME    = "MP160"
_SUPPORTED = {"MP150": 101, "MP160": 103, "MP36R": 103}
DEVCODE    = _SUPPORTED[DEVNAME]

GAIN_SCALE = 5          # hardware gain on CH2

N_ANALOG      = 2
DIGITAL_LINES = [9, 11, 12, 13, 14]   # BIOPAC digital lines to listen to
N_DIGITAL     = len(DIGITAL_LINES)
N_CHANNELS    = N_ANALOG + N_DIGITAL

SAMPLERATE_HZ    = 1000
SAMPLETIME_MS    = 1000.0 / float(SAMPLERATE_HZ)

SAMPLES_PER_CALL  = 100
NUM_DOUBLES_REQ   = N_CHANNELS * SAMPLES_PER_CALL

RT_WINDOW_S   = 10.0
RT_MAX_POINTS = int(RT_WINDOW_S * SAMPLERATE_HZ)

YLIM_CH1     = (2.0,  15.0)
YLIM_CH2     = (-5.0,  5.0)
DRAW_EVERY_S = 0.05

# ═══════════════════════════════════════════════════════════════════════════════
#  DIGITAL TRIGGER  (parallel port via inpoutx64.dll)
# ═══════════════════════════════════════════════════════════════════════════════

TRIGGER_PORT  = 0x3FE8
TRIGGER_BYTE  = 0xFF
RESET_BYTE    = 0x00
PULSE_S       = 0.050

# ═══════════════════════════════════════════════════════════════════════════════
#  EYELINK
# ═══════════════════════════════════════════════════════════════════════════════

DUMMY_MODE = False
SCREEN_W   = 1920
SCREEN_H   = 1200

EYELINK_IP = "100.1.1.1"

# ═══════════════════════════════════════════════════════════════════════════════
#  RTBOX
# ═══════════════════════════════════════════════════════════════════════════════

RTBOX_PORT     = "COM4"
RTBOX_BAUD     = 115200
RTBOX_CLOCK_HZ = 921600.0
RTBOX_ENABLE   = 0b00001001   # bit0 = press, bit3 = light

# Serial code → (button name, TTL value sent to BIOPAC)
RTBOX_EVENT_MAP: dict[int, tuple[str, int]] = {
    49: ("1",     1),    # Btn1 press → TTL 1
    51: ("2",     2),    # Btn2 press → TTL 2
    53: ("3",     4),    # Btn3 press → TTL 4
    55: ("4",     8),    # Btn4 press → TTL 8
    48: ("light", 32),   # Light event → TTL 32 (D9 BIOPAC)
}

# ═══════════════════════════════════════════════════════════════════════════════
#  STROOP TASK
# ═══════════════════════════════════════════════════════════════════════════════

N_BLOCKS  = 2
N_TRIALS  = 5
FIX_MIN   = 0.500   # seconds
FIX_MAX   = 1.000

# Response keys: pygame key constant → label string  (mapping done in stroop.py)
RESP_KEY_LABELS = {
    "v": "v",
    "b": "b",
    "n": "n",
}

COLORS_RGB: dict[str, tuple[int, int, int]] = {
    "RED":   (220,  50,  50),
    "GREEN": ( 50, 200,  80),
    "BLUE":  ( 60, 140, 255),
}

INCONGRUENT_STIMULI: list[tuple[str, str]] = [
    ("RED",   "GREEN"),
    ("RED",   "BLUE"),
    ("GREEN", "RED"),
    ("GREEN", "BLUE"),
    ("BLUE",  "RED"),
    ("BLUE",  "GREEN"),
]

# ═══════════════════════════════════════════════════════════════════════════════
#  UI COLOURS  (pygame RGB tuples)
# ═══════════════════════════════════════════════════════════════════════════════

C_BG         = ( 23,  25,  26)
C_BORDER     = ( 52,  54,  62)
C_ACCENT     = ( 99, 102, 241)
C_ACCENT_LT  = (139, 141, 240)
C_LAVENDER   = (230, 203, 251)
C_MUTED      = (110, 112, 128)
C_WHITE      = (228, 228, 238)
C_DISABLED   = ( 34,  36,  38)
C_DISABLED_T = ( 72,  74,  84)
C_DONE_BG    = ( 40,  38,  60)
C_DONE_FG    = C_LAVENDER
