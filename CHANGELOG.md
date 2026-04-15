# Changelog

All notable changes to OpenPhysioHub are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.1.0] — 2026-04-15

### Added
- Initial public release.
- `openphysiohub/config.py` — centralised hardware and task constants
  (EyeLink IP, RTBox COM port, BIOPAC channel config, Stroop parameters,
  UI colours).
- `openphysiohub/biopac.py` — BIOPAC MP160 acquisition via `mpdev.dll`
  (connect, configure, read chunks, disconnect).
- `openphysiohub/trigger.py` — digital TTL pulse output via `inpoutx64.dll`
  (parallel port).
- `openphysiohub/rtbox.py` — RTBox serial thread; reads button events,
  forwards TTL to BIOPAC, stores events for the Stroop loop.
- `openphysiohub/eyelink.py` — EyeLink connection, recording configuration,
  pygame calibration/validation UI, `DummyDisplay` fallback.
- `openphysiohub/eda_calibration.py` — tkinter dialog for 2 s EDA baseline
  recording; returns median CH1 offset.
- `openphysiohub/stroop.py` — Stroop colour-word task (2 blocks × 5
  incongruent trials); returns `(stroop_events, gaze_samples)`.
- `openphysiohub/main.py` — experiment orchestrator; manages BIOPAC
  acquisition thread, matplotlib rolling plot (main thread), and Stroop
  thread; writes JSON output.
- `final.py` — legacy entry point shim forwarding to `openphysiohub.main`.
- `pyproject.toml` — installable package (`pip install -e .`).
- `LICENSE` — MIT.
- `CONTRIBUTING.md`, `CHANGELOG.md`, `CLAUDE.md`.
- `README.md` stubs in each third-party library directory with download
  instructions for proprietary files.
- `.gitignore` excluding all proprietary and participant data files.
