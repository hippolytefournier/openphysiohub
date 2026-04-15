# Contributing to OpenPhysioHub

Thank you for your interest in contributing. This document explains how to
report bugs, suggest improvements, and submit code changes.

---

## Reporting bugs and requesting features

Use the [GitHub issue tracker](../../issues) to report bugs or request new
features. Before opening a new issue, search existing issues to avoid
duplicates.

When reporting a bug, please include:

- Your operating system and Python version
- The hardware you are using (BIOPAC model, EyeLink model, RTBox firmware version)
- A minimal description of what you expected vs. what happened
- Any error messages or tracebacks

---

## Submitting changes

1. Fork the repository and create a branch from `main`:
   ```bash
   git checkout -b fix/your-description
   ```

2. Make your changes. Keep each pull request focused on a single fix or
   feature.

3. Run the tests before submitting:
   ```bash
   pip install -e .
   pytest tests/
   ```

4. Push your branch and open a pull request against `main`. Describe what
   the change does and why.

---

## Hardware-dependent code

Most modules (`biopac.py`, `trigger.py`, `eyelink.py`) require physical
hardware to run. If you are contributing changes to these modules and do not
have the hardware available, please note this clearly in your pull request.
Reviewers with the hardware will test before merging.

---

## Code style

- Follow the existing style (PEP 8, 4-space indentation).
- All constants go in `config.py`.
- Do not introduce new module-level globals with mutable state.
- Keep each module focused on a single hardware subsystem or task component.

---

## AI usage disclosure

Contributors who use generative AI tools (e.g. GitHub Copilot, ChatGPT,
Claude) to assist with code or documentation must disclose this in their
pull request description, naming the tool and the scope of use.

---

## Questions

Open an issue with the label `question` if you are unsure about anything.
