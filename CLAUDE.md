# OpenPhysioHub — Claude Context

## What this project is
A Python experiment package for experimental psychology.
Runs a Stroop colour-word task with synchronised BIOPAC (EDA/ECG),
SR Research EyeLink (eye tracking), and RTBox (button responses).
Saves time-stamped JSON at the end of the session.

## History
Refactored from a single monolithic `final.py` into a proper Python package.
`final.py` is now a two-line shim that calls `openphysiohub.main:main()`.

## Package structure
```
openphysiohub/
  config.py           all constants — edit here for hardware setup
  biopac.py           BIOPAC MP160 via mpdev.dll (ctypes)
  trigger.py          TTL pulses via inpoutx64.dll (parallel port)
  rtbox.py            RTBox serial thread
  eyelink.py          EyeLink connection + pygame calibration UI
  eda_calibration.py  EDA baseline tkinter dialog
  stroop.py           Stroop task — returns (stroop_events, gaze_samples)
  main.py             orchestrator + acquisition thread + matplotlib plot
```

## Proprietary files (gitignored — must be placed manually)
- `eye_tracking_library/CalibrationGraphicsPygame.py` + `*.wav` — SR Research
- `biopac_input_library/inpoutx64.dll` — InpOut32
- `button_box_library/RTBox.py` — xiangruili/RTBox_py (no license)
- `biopac_library/mpydev.py` — PyGaze GPL v3 (reference only, not imported)
- `mpdev.dll` — BIOPAC, system-installed

## Key design decisions
- All constants centralised in `config.py` (including EYELINK_IP, RTBOX_PORT, TRIGGER_PORT)
- `run_eyelink_calibration()` returns `calib_info` dict (no global)
- `run_stroop()` returns `(stroop_events, gaze_samples)` (no globals)
- `biopac_samples` is a local list in `main()`
- matplotlib MUST run in the main thread on Windows
- `os.chdir(LIB_ET_DIR)` is called in `main()` before CalibrationGraphics init

## Hardware parameters to adjust per machine (config.py)
- `EYELINK_IP` — default "100.1.1.1"
- `RTBOX_PORT` — default "COM4"
- `TRIGGER_PORT` — default 0x3FE8
- `BIOPAC_DLL_PATH` — default standard BIOPAC install path
- `DUMMY_MODE` — set True to run without EyeLink hardware

## Running
```bash
python final.py
# or
python -m openphysiohub.main
```

## Install
```bash
pip install -e .
pip install numpy pyserial pygame matplotlib
```
