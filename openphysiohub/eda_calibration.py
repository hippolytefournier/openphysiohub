"""
eda_calibration.py
──────────────────
EDA baseline calibration — tkinter dialog.

Records 2 s of BIOPAC CH1 with leads disconnected from the participant,
computes the median raw value, and returns it as the cal offset used by
biopac_read_chunk throughout the rest of the session.

Public API
──────────
    eda_calibration_box()   show dialog, return cal value (float)
"""

import sys
import time
import tkinter as tk
from tkinter import ttk

import numpy as np
from ctypes import c_double, c_uint32, byref

from .config import NUM_DOUBLES_REQ, N_CHANNELS
from .biopac import biopac_start, biopac_stop_disconnect, biopac_read_chunk, mpdev


# ═══════════════════════════════════════════════════════════════════════════════

def eda_calibration_box() -> float:
    """
    Open the EDA calibration dialog.

    Records 2 s of BIOPAC CH1 baseline (leads connected to amplifier but
    NOT to the participant), computes the median raw value, and returns it
    as the cal offset for the rest of the session.

    Exits the process if the user cancels.
    """
    CAL_DURATION  = 2.0
    result_holder = {"cal": None, "ok": False}

    root = tk.Tk()
    root.title("EDA Calibration")
    root.geometry("520x300")
    root.configure(bg="#17191a")
    root.resizable(False, False)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TLabel",        background="#17191a", foreground="#e4e4ee",
                    font=("Segoe UI", 11))
    style.configure("TButton",       font=("Segoe UI", 11, "bold"), padding=8)
    style.configure("Accent.TButton", foreground="white", background="#6366f1")

    instr_text = (
        "Connect the electrode leads to the EDA,\n"
        "but do NOT connect the leads to the electrodes\n"
        "and participant.\n\n"
        'Click "Calibrate" when ready.'
    )
    ttk.Label(root, text=instr_text, justify="center").pack(pady=(24, 10))

    lbl_status      = ttk.Label(root, text="",
                                foreground="#7da8ff", font=("Segoe UI", 10))
    lbl_status.pack()
    lbl_val_display = ttk.Label(root, text="",
                                foreground="#e6cbfb", font=("Segoe UI", 13, "bold"))
    lbl_val_display.pack(pady=4)

    btn_frame = tk.Frame(root, bg="#17191a")
    btn_frame.pack(pady=16)

    def do_calibrate():
        btn_calib.config(state="disabled")
        btn_validate.pack_forget()
        lbl_status.config(text="Recording 2 s CH1 baseline…")
        root.update()

        ch1_vals  = []
        cbuf_cal  = (c_double * NUM_DOUBLES_REQ)()
        numrec    = c_uint32(0)
        try:
            biopac_start()
            t0 = time.perf_counter()
            while (time.perf_counter() - t0) < CAL_DURATION:
                # Advance the hardware buffer (result discarded — we need raw values
                # before the np.interp transform, so we read cbuf directly below)
                biopac_read_chunk(cbuf_cal, numrec, t0, 0.0)

                # Second read: collect raw CH1 before the interp transform
                numrec.value = 0
                rc = mpdev.receiveMPData(
                    cbuf_cal, c_uint32(NUM_DOUBLES_REQ), byref(numrec)
                )
                n_frames = int(numrec.value) // N_CHANNELS
                for fi in range(n_frames):
                    ch1_vals.append(float(cbuf_cal[fi * N_CHANNELS + 0]))
                time.sleep(0.005)
        finally:
            biopac_stop_disconnect()

        median_val = float(np.median(ch1_vals)) if ch1_vals else 0.005
        result_holder["cal"] = median_val
        lbl_status.config(text="Calibration terminée.")
        lbl_val_display.config(
            text=f"Valeur cal (médiane CH1) = {median_val:.6f}"
        )
        btn_calib.config(state="normal", text="Recommencer")
        btn_validate.pack(in_=btn_frame, side="left", padx=10)
        root.update()

    def do_validate():
        result_holder["ok"] = True
        root.destroy()

    def do_cancel():
        root.destroy()

    btn_calib = ttk.Button(btn_frame, text="Calibrate",
                           command=do_calibrate, style="Accent.TButton")
    btn_calib.pack(side="left", padx=10)

    btn_validate = ttk.Button(btn_frame, text="Valider", command=do_validate)
    # shown only after a successful calibration run

    ttk.Button(btn_frame, text="Cancel", command=do_cancel).pack(
        side="left", padx=10
    )

    root.mainloop()

    if not result_holder["ok"] or result_holder["cal"] is None:
        print("EDA calibration annulée. Arrêt.")
        sys.exit(0)

    return result_holder["cal"]
