"""
main.py
───────
Experiment entry point and acquisition / plot orchestration.

Pipeline
────────
  1. Connect EyeLink
  2. pygame init + EyeLink calibration UI
  3. EDA calibration (tkinter)
  4. Start BIOPAC acquisition + RTBox serial thread + EyeLink recording
  5. Stroop task  (dedicated thread — pygame + EyeLink)
     matplotlib rolling plot  (main thread — required on Windows)
     BIOPAC acquisition  (dedicated thread)
  6. Stop all hardware, save JSON
"""

import os
import sys
import json
import time
import signal
import threading
import collections

import numpy as np
import pylink
import pygame
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from ctypes import c_double, c_uint32

from .config import (
    LIB_ET_DIR,
    DATA_DIR,
    SCREEN_W, SCREEN_H,
    SAMPLERATE_HZ,
    N_CHANNELS, N_ANALOG, DIGITAL_LINES,
    NUM_DOUBLES_REQ,
    RT_WINDOW_S, RT_MAX_POINTS,
    YLIM_CH1, YLIM_CH2, DRAW_EVERY_S,
    GAIN_SCALE,
    C_BG, C_LAVENDER,
)
from .biopac import biopac_start, biopac_stop_disconnect, mpdev
from .trigger import reset_trigger
from .rtbox import rtbox_open, rtbox_close
from .eyelink import (
    connect_eyelink, run_eyelink_calibration,
    DummyDisplay, CalibrationGraphics,
)
from .eda_calibration import eda_calibration_box
from .stroop import run_stroop


# ═══════════════════════════════════════════════════════════════════════════════
#  JSON output
# ═══════════════════════════════════════════════════════════════════════════════

def _save_json(
    cal_value: float,
    calib_info: dict,
    stroop_events: list,
    gaze_samples: list,
    biopac_samples: list,
) -> None:
    ts = time.strftime("%Y%m%d_%H%M%S")

    et_path = DATA_DIR / f"eyetracker_{ts}.json"
    with open(et_path, "w") as f:
        json.dump({
            "meta": {
                "date":        time.strftime("%Y-%m-%d %H:%M:%S"),
                "sample_rate": SAMPLERATE_HZ,
                "screen_w":    SCREEN_W,
                "screen_h":    SCREEN_H,
                "n_samples":   len(gaze_samples),
            },
            "calibration_info": calib_info,
            "stroop_events":    stroop_events,
            "samples":          gaze_samples,
        }, f, indent=2)
    print(f"[JSON] Eye-tracker : {et_path}")

    bio_path = DATA_DIR / f"biopac_{ts}.json"
    with open(bio_path, "w") as f:
        json.dump({
            "meta": {
                "date":        time.strftime("%Y-%m-%d %H:%M:%S"),
                "sample_rate": SAMPLERATE_HZ,
                "cal_value":   cal_value,
                "n_samples":   len(biopac_samples),
            },
            "samples": biopac_samples,
        }, f, indent=2)
    print(f"[JSON] BIOPAC : {bio_path}")


# ═══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:

    # ── 1. EyeLink connection ─────────────────────────────────────────────────
    print("\n=== [1] Connexion EyeLink ===")
    el = connect_eyelink()

    # ── 2. pygame + EyeLink calibration ──────────────────────────────────────
    print("\n=== [2] Calibration EyeLink ===")
    pygame.init()
    pygame.mixer.init()
    win = pygame.display.set_mode(
        (SCREEN_W, SCREEN_H), pygame.FULLSCREEN | pygame.DOUBLEBUF
    )
    pygame.display.set_caption("Experiment")
    pygame.mouse.set_visible(True)

    F = {
        "title" : pygame.font.SysFont("Segoe UI", 46, bold=True),
        "sub"   : pygame.font.SysFont("Segoe UI", 21),
        "btn"   : pygame.font.SysFont("Segoe UI", 26, bold=True),
        "hint"  : pygame.font.SysFont("Segoe UI", 18),
        "tag"   : pygame.font.SysFont("Segoe UI", 15, bold=True),
        "instr" : pygame.font.SysFont("Segoe UI", 28),
        "badge" : pygame.font.SysFont("Segoe UI", 16, bold=True),
        "key"   : pygame.font.SysFont("Consolas",  26, bold=True),
    }

    # CalibrationGraphics needs cwd = LIB_ET_DIR to find sound files by
    # relative path (same requirement as the original final.py line 58)
    os.chdir(LIB_ET_DIR)

    genv = CalibrationGraphics(el, win)
    genv.setCalibrationColors(C_LAVENDER, C_BG)
    genv.setTargetType("circle")
    genv.setCalibrationSounds("type.wav", "qbeep.wav", "error.wav")
    pylink.openGraphicsEx(genv)

    calib_info = run_eyelink_calibration(el, win, F)

    pylink.closeGraphics()
    print("[ET] Calibration terminée.")

    dummy = DummyDisplay()
    pylink.openGraphicsEx(dummy)
    pygame.display.iconify()

    # ── 3. EDA calibration ────────────────────────────────────────────────────
    print("\n=== [3] Calibration EDA ===")
    cal = eda_calibration_box()
    print(f"[EDA] cal = {cal:.6f}")

    # ── 4. Start acquisitions ─────────────────────────────────────────────────
    print("\n=== [4] Démarrage acquisitions ===")
    biopac_start()
    print("[BIOPAC] Acquisition démarrée.")

    rtbox_open()

    el.setOfflineMode()
    pylink.msecDelay(200)
    el.startRecording(0, 0, 1, 0)
    pylink.pumpDelay(100)
    print("[ET] Recording EyeLink démarré.")

    experiment_t0 = time.perf_counter()

    # ── 5. Stroop in a dedicated thread ───────────────────────────────────────
    print("\n=== [5] Tâche Stroop ===")
    win = pygame.display.set_mode(
        (SCREEN_W, SCREEN_H), pygame.FULLSCREEN | pygame.DOUBLEBUF
    )
    pygame.display.set_caption("Stroop")
    pygame.mouse.set_visible(False)
    pygame.event.clear()
    F["title"] = pygame.font.SysFont("Segoe UI", 72, bold=True)

    stroop_done  = threading.Event()
    stroop_error = [None]
    stroop_result: list = [[], []]   # [stroop_events, gaze_samples]

    def stroop_thread_fn():
        try:
            stroop_result[0], stroop_result[1] = run_stroop(
                win, F, el, cal, experiment_t0
            )
        except Exception as e:
            stroop_error[0] = e
        finally:
            stroop_done.set()

    stroop_thread = threading.Thread(target=stroop_thread_fn, daemon=True)
    stroop_thread.start()

    # ── BIOPAC acquisition thread ─────────────────────────────────────────────
    biopac_samples: list[dict] = []
    acq_error = [None]

    _buf_lock = threading.Lock()
    _buf_t    = collections.deque(maxlen=RT_MAX_POINTS)
    _buf_ch1  = collections.deque(maxlen=RT_MAX_POINTS)
    _buf_ch2  = collections.deque(maxlen=RT_MAX_POINTS)
    _buf_digs = {f"d{dl}": collections.deque(maxlen=RT_MAX_POINTS)
                 for dl in DIGITAL_LINES}

    def acq_thread_fn():
        from ctypes import byref
        cbuf_        = (c_double * NUM_DOUBLES_REQ)()
        numreceived_ = c_uint32(0)
        sample_i     = 0
        try:
            while not stroop_done.is_set():
                numreceived_.value = 0
                rc = mpdev.receiveMPData(
                    cbuf_, c_uint32(NUM_DOUBLES_REQ), byref(numreceived_)
                )
                if int(rc) != 1:
                    continue

                n_frames = int(numreceived_.value) // N_CHANNELS
                for frame_i in range(n_frames):
                    base    = frame_i * N_CHANNELS
                    ch1_raw = float(cbuf_[base + 0])
                    ch2_raw = float(cbuf_[base + 1]) if N_ANALOG >= 2 else float("nan")

                    digs = {}
                    for di, dl in enumerate(DIGITAL_LINES):
                        raw = float(cbuf_[base + N_ANALOG + di])
                        digs[f"d{dl}"] = 1 if raw >= 0.5 else 0

                    ch1      = np.interp(ch1_raw, [0 + cal, 100 + cal], [0, 500])
                    ch2      = ch2_raw / GAIN_SCALE
                    t_sample = sample_i / float(SAMPLERATE_HZ)

                    row = {"t": t_sample, "ch1": ch1, "ch2": ch2}
                    row.update(digs)
                    biopac_samples.append(row)

                    with _buf_lock:
                        _buf_t.append(t_sample)
                        _buf_ch1.append(ch1)
                        _buf_ch2.append(ch2)
                        for key, val in digs.items():
                            _buf_digs[key].append(val)

                    sample_i += 1
        except Exception as e:
            acq_error[0] = e

    acq_th = threading.Thread(target=acq_thread_fn, daemon=True)
    acq_th.start()

    # ── matplotlib rolling plot (must run in main thread on Windows) ──────────
    n_digital = len(DIGITAL_LINES)
    plt.ion()
    fig, axes = plt.subplots(
        2 + n_digital, 1, sharex=True, figsize=(10, 4 + 2 * n_digital)
    )
    ax1, ax2 = axes[0], axes[1]
    dig_axes = axes[2:]

    (line1,) = ax1.plot([], [], lw=1)
    ax1.set_ylabel("CH1")
    ax1.set_title("BIOPAC Real-time rolling window (last 10 s)")
    ax1.set_ylim(*YLIM_CH1)
    ax1.grid(True)

    (line2,) = ax2.plot([], [], lw=1)
    ax2.set_ylabel("CH2 (Volts)")
    ax2.set_ylim(*YLIM_CH2)
    ax2.grid(True)

    dig_lines = {}
    for ax_d, dl in zip(dig_axes, DIGITAL_LINES):
        key   = f"d{dl}"
        (ln,) = ax_d.plot([], [], lw=1, drawstyle="steps-post")
        ax_d.set_ylabel(f"D{dl}")
        ax_d.set_ylim(-0.2, 1.2)
        ax_d.set_yticks([0, 1])
        ax_d.grid(True)
        dig_lines[key] = (ax_d, ln)

    dig_axes[-1].set_xlabel("Time (s)")
    fig.tight_layout()
    fig.show()

    try:
        while not stroop_done.is_set():
            with _buf_lock:
                t_arr    = list(_buf_t)
                ch1_arr  = list(_buf_ch1)
                ch2_arr  = list(_buf_ch2)
                digs_arr = {k: list(v) for k, v in _buf_digs.items()}

            if t_arr:
                line1.set_data(t_arr, ch1_arr)
                line2.set_data(t_arr, ch2_arr)
                for key, (ax_d, ln) in dig_lines.items():
                    ln.set_data(t_arr, digs_arr[key])

                y = np.asarray(ch1_arr, dtype=float)
                y = y[np.isfinite(y)]
                if y.size:
                    y_std = float(y.std())
                    ax1.set_ylim(
                        float(y.min()) - 0.5 * y_std,
                        float(y.max()) + 0.5 * y_std,
                    )

                x0 = max(0.0, t_arr[-1] - RT_WINDOW_S)
                x1 = t_arr[-1]
                ax1.set_xlim(x0, x1)
                ax2.set_xlim(x0, x1)
                for ax_d, _ in dig_lines.values():
                    ax_d.set_xlim(x0, x1)

            fig.canvas.draw_idle()
            plt.pause(DRAW_EVERY_S)

    finally:
        plt.ioff()
        try:
            plt.close(fig)
        except Exception:
            pass

        # ── 6. Stop & save ────────────────────────────────────────────────────
        try:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
        except Exception:
            pass

        print("\n=== [6] Arrêt & sauvegarde ===")

        try:
            stroop_done.wait(timeout=3.0)
        except Exception:
            pass

        try:
            acq_th.join(timeout=2.0)
        except Exception:
            pass

        try:
            biopac_stop_disconnect()
            print("[BIOPAC] Arrêt.")
        except Exception as e:
            print(f"[BIOPAC] Erreur arrêt : {e}")

        try:
            rtbox_close()
        except Exception as e:
            print(f"[RTBox] Erreur fermeture : {e}")

        try:
            el.stopRecording()
            pylink.msecDelay(100)
            el.setOfflineMode()
            pylink.msecDelay(200)
            el.closeDataFile()
            el.close()
            print("[ET] Arrêt.")
        except Exception as e:
            print(f"[ET] Erreur arrêt : {e}")

        try:
            reset_trigger()
            print("[TRIGGER] Port remis à 0.")
        except Exception as e:
            print(f"[TRIGGER] Erreur reset : {e}")

        try:
            pygame.quit()
        except Exception:
            pass

        if stroop_error[0]:
            print(f"[ERREUR Stroop] {stroop_error[0]}")
        if acq_error[0]:
            print(f"[ERREUR Acquisition] {acq_error[0]}")

        _save_json(
            cal_value      = cal,
            calib_info     = calib_info,
            stroop_events  = stroop_result[0],
            gaze_samples   = stroop_result[1],
            biopac_samples = biopac_samples,
        )
        print("\n✓ Expérience terminée.")


if __name__ == "__main__":
    main()
