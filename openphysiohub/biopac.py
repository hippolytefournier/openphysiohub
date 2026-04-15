"""
biopac.py
─────────
BIOPAC MP-series acquisition via mpdev.dll.

Public API
──────────
    biopac_start()                          connect + configure + start acquisition
    biopac_stop_disconnect()                stop acquisition + disconnect
    biopac_read_chunk(cbuf, numreceived,    read one block of samples
                      t0, cal_value)
"""

import time
import numpy as np
from ctypes import windll, c_int, c_double, c_uint32, byref

from .config import (
    BIOPAC_DLL_PATH,
    DEVCODE,
    SAMPLETIME_MS,
    N_ANALOG,
    N_CHANNELS,
    DIGITAL_LINES,
    N_DIGITAL,
    NUM_DOUBLES_REQ,
    GAIN_SCALE,
)

# ── Windows 1 ms timer ───────────────────────────────────────────────────────
_winmm = windll.LoadLibrary("winmm")

# ── BIOPAC DLL ───────────────────────────────────────────────────────────────
mpdev = windll.LoadLibrary(BIOPAC_DLL_PATH)


# ═══════════════════════════════════════════════════════════════════════════════

def biopac_start() -> None:
    """connectMPDev + configure channels + startAcquisition."""
    _winmm.timeBeginPeriod(1)

    rc = mpdev.connectMPDev(c_int(DEVCODE), c_int(11), b"auto")
    if int(rc) != 1:
        _winmm.timeEndPeriod(1)
        raise RuntimeError(f"connectMPDev failed (rc={int(rc)})")

    rc = mpdev.setSampleRate(c_double(SAMPLETIME_MS))
    if int(rc) != 1:
        raise RuntimeError(f"setSampleRate failed (rc={int(rc)})")

    channels = [1] * N_ANALOG + [0] * (16 - N_ANALOG)
    ch_arr = (c_int * 16)(*channels)
    rc = mpdev.setAcqChannels(byref(ch_arr))
    if int(rc) != 1:
        raise RuntimeError(f"setAcqChannels failed (rc={int(rc)})")

    digital_channels = [0] * 16
    for dl in DIGITAL_LINES:
        digital_channels[int(dl)] = 1
    d_arr = (c_int * 16)(*digital_channels)
    rc = mpdev.setDigitalAcqChannels(byref(d_arr))
    if int(rc) != 1:
        raise RuntimeError(f"setDigitalAcqChannels failed (rc={int(rc)})")

    try:
        rc = mpdev.startMPAcqDaemon()
        if int(rc) != 1:
            raise RuntimeError(f"startMPAcqDaemon failed (rc={int(rc)})")
    except AttributeError:
        pass  # not available on all firmware versions

    rc = mpdev.startAcquisition()
    if int(rc) != 1:
        raise RuntimeError(f"startAcquisition failed (rc={int(rc)})")


def biopac_stop_disconnect() -> None:
    """stopAcquisition + disconnectMPDev + release 1 ms timer."""
    try:
        mpdev.stopAcquisition()
    except Exception:
        pass
    mpdev.disconnectMPDev()
    _winmm.timeEndPeriod(1)


def biopac_read_chunk(
    cbuf,
    numreceived: c_uint32,
    t0: float,
    cal_value: float,
) -> list[dict]:
    """
    Read one block of samples from the BIOPAC.

    Parameters
    ----------
    cbuf        : ctypes c_double array of length NUM_DOUBLES_REQ
    numreceived : c_uint32 output counter (reset to 0 before call)
    t0          : perf_counter reference time for the recording session
    cal_value   : EDA baseline offset (median CH1 from calibration)

    Returns
    -------
    List of dicts, one per sample frame:
        {"t": float, "ch1": float, "ch2": float, "d9": int, "d11": int, ...}
    """
    numreceived.value = 0
    rc = mpdev.receiveMPData(cbuf, c_uint32(NUM_DOUBLES_REQ), byref(numreceived))
    if int(rc) != 1:
        raise RuntimeError(f"receiveMPData failed (rc={int(rc)})")

    n_frames = int(numreceived.value) // N_CHANNELS
    rows = []

    for frame_i in range(n_frames):
        base = frame_i * N_CHANNELS
        ch1_raw = float(cbuf[base + 0])
        ch2_raw = float(cbuf[base + 1]) if N_ANALOG >= 2 else float("nan")

        digs = {}
        for di, dl in enumerate(DIGITAL_LINES):
            raw = float(cbuf[base + N_ANALOG + di])
            digs[f"d{dl}"] = 1 if raw >= 0.5 else 0

        ch1 = np.interp(ch1_raw, [0 + cal_value, 100 + cal_value], [0, 500])
        ch2 = ch2_raw / GAIN_SCALE
        t_sample = time.perf_counter() - t0

        row = {"t": t_sample, "ch1": ch1, "ch2": ch2}
        row.update(digs)
        rows.append(row)

    return rows
