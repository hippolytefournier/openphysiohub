"""
final.py — legacy entry point, kept for backwards compatibility.
The experiment is now packaged in openphysiohub/.

Run with:
    python final.py
    python -m openphysiohub.main
    openphysiohub          (after pip install -e .)
"""

from openphysiohub.main import main

if __name__ == "__main__":
    main()
