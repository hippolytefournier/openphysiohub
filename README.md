# OpenPhysioHub

A Python package for physiological signal acquisition and synchronised stimulus delivery in experimental psychology research.

---

## Overview

OpenPhysioHub runs a multi-modal experiment pipeline combining EDA/ECG acquisition (BIOPAC), eye tracking (SR Research EyeLink), button responses (RTBox), and a Stroop colour-word task (pygame). All signals are time-stamped against a common clock and saved as JSON at the end of the session.

**Pipeline:**

1. EyeLink calibration and validation
2. EDA baseline calibration (tkinter dialog)
3. BIOPAC + EyeLink + RTBox acquisition start
4. Stroop task (2 blocks × 5 incongruent trials)
5. Real-time rolling plot of BIOPAC signals
6. JSON export — eye-tracker samples + BIOPAC samples + event log

---

## Installation

```bash
git clone https://github.com/your-org/OpenPhysioHub.git
cd OpenPhysioHub
pip install -e .
pip install numpy pyserial pygame matplotlib
```

**Requirements:** Python 3.9+, Windows (required by BIOPAC and InpOut32 drivers)

---

## Hardware Setup

This package requires several proprietary drivers that cannot be
redistributed. Before running the experiment, obtain and place the
following files manually.

### EyeLink (SR Research)

Install the **EyeLink Developers Kit** from https://www.sr-support.com/
then copy into `eye_tracking_library/`:

- `CalibrationGraphicsPygame.py`
- `type.wav`, `qbeep.wav`, `error.wav`

Install the Python wrapper:

```bash
pip install pylink-sr-research
```

### BIOPAC

Install the **BIOPAC Hardware API 2.2 Research** from https://www.biopac.com/
This places `mpdev.dll` system-wide — no manual copy needed.

### Parallel port trigger (InpOut32)

Download the DLLs from https://www.highrez.co.uk/downloads/inpout32/
and place `inpoutx64.dll` in `biopac_input_library/`.

### RTBox

Download `RTBox.py` from https://github.com/xiangruili/RTBox_py
and place it in `button_box_library/` (used as reference only — not
imported at runtime).

---

## Configuration

All hardware parameters are in `openphysiohub/config.py`. Edit before running:

| Parameter | Default | Description |
|---|---|---|
| `EYELINK_IP` | `"100.1.1.1"` | EyeLink tracker IP address |
| `RTBOX_PORT` | `"COM4"` | RTBox serial port |
| `TRIGGER_PORT` | `0x3FE8` | Parallel port address |
| `BIOPAC_DLL_PATH` | `C:\Program Files (x86)\...` | Path to mpdev.dll |
| `DUMMY_MODE` | `False` | Set to `True` to run without EyeLink hardware |

---

## Running the experiment

```bash
python final.py
```

Or equivalently:

```bash
python -m openphysiohub.main
```

Output files are saved to `data/` as:
- `eyetracker_YYYYMMDD_HHMMSS.json`
- `biopac_YYYYMMDD_HHMMSS.json`

---

## Project Structure

```
OpenPhysioHub/
├── final.py                    entry point (legacy shim)
├── openphysiohub/
│   ├── config.py               all hardware and task constants
│   ├── biopac.py               BIOPAC acquisition via mpdev.dll
│   ├── trigger.py              digital TTL pulses via inpoutx64.dll
│   ├── rtbox.py                RTBox serial thread
│   ├── eyelink.py              EyeLink connection and calibration UI
│   ├── eda_calibration.py      EDA baseline tkinter dialog
│   ├── stroop.py               Stroop colour-word task
│   └── main.py                 experiment orchestrator
├── eye_tracking_library/       place SR Research files here (see README)
├── biopac_input_library/       place inpoutx64.dll here (see README)
├── button_box_library/         place RTBox.py here (see README)
├── biopac_library/             mpydev.py reference (not used at runtime)
└── pyproject.toml
```

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Submit a pull request

For bug reports and feature requests, open an issue on GitHub.

---

## Affiliation

OpenPhysioHub is developed at the [Laboratory for Experimental Research in Behavior (LERB)](https://www.unil.ch/ssp/fr/home/ressources/espaces/espace-chercheur-euses/infrastructures/lerb.html), University of Lausanne (UNIL), Switzerland.

---

## Citation

If you use OpenPhysioHub in published research, please cite:

```bibtex
@software{openphysiohub,
  title       = {{OpenPhysioHub}: A Python package for physiological data acquisition in experimental psychology},
  author      = {Fournier, Hippolyte and Ruggeri, Paolo and Dan-Glauser, Elise},
  year        = {2026},
  institution = {Laboratory for Experimental Research in Behavior (LERB), University of Lausanne},
  url         = {https://github.com/hippolytefournier/openphysiohub}
}
```

---

## License

OpenPhysioHub is released under the [MIT License](LICENSE).
