"""
tests/test_config.py
────────────────────
Tests for openphysiohub.config — the only module that can be imported
without physical hardware or proprietary DLLs.
"""

import pytest
from pathlib import Path


# ── Import ────────────────────────────────────────────────────────────────────

from openphysiohub.config import (
    PROJECT_ROOT,
    LIB_ET_DIR, LIB_BIOPAC_DIR, LIB_RTBOX_DIR, DATA_DIR,
    DEVCODE, DEVNAME, _SUPPORTED,
    N_ANALOG, DIGITAL_LINES, N_DIGITAL, N_CHANNELS,
    SAMPLERATE_HZ, SAMPLETIME_MS,
    SAMPLES_PER_CALL, NUM_DOUBLES_REQ,
    RT_WINDOW_S, RT_MAX_POINTS,
    TRIGGER_PORT, TRIGGER_BYTE, RESET_BYTE, PULSE_S,
    RTBOX_CLOCK_HZ, RTBOX_EVENT_MAP, RTBOX_ENABLE,
    N_BLOCKS, N_TRIALS, FIX_MIN, FIX_MAX,
    INCONGRUENT_STIMULI, COLORS_RGB,
    C_BG, C_WHITE, C_LAVENDER,
)


# ── Paths ─────────────────────────────────────────────────────────────────────

class TestPaths:
    def test_project_root_is_path(self):
        assert isinstance(PROJECT_ROOT, Path)

    def test_project_root_exists(self):
        assert PROJECT_ROOT.exists()

    def test_lib_dirs_are_under_project_root(self):
        for d in (LIB_ET_DIR, LIB_BIOPAC_DIR, LIB_RTBOX_DIR, DATA_DIR):
            assert str(d).startswith(str(PROJECT_ROOT))

    def test_data_dir_created(self):
        assert DATA_DIR.exists()


# ── BIOPAC ────────────────────────────────────────────────────────────────────

class TestBiopacConfig:
    def test_devcode_matches_devname(self):
        assert DEVCODE == _SUPPORTED[DEVNAME]

    def test_channel_counts(self):
        assert N_DIGITAL == len(DIGITAL_LINES)
        assert N_CHANNELS == N_ANALOG + N_DIGITAL

    def test_sampletime(self):
        assert SAMPLETIME_MS == pytest.approx(1000.0 / SAMPLERATE_HZ)

    def test_num_doubles_req(self):
        assert NUM_DOUBLES_REQ == N_CHANNELS * SAMPLES_PER_CALL

    def test_rt_max_points(self):
        assert RT_MAX_POINTS == int(RT_WINDOW_S * SAMPLERATE_HZ)

    def test_digital_lines_unique(self):
        assert len(DIGITAL_LINES) == len(set(DIGITAL_LINES))


# ── Trigger ───────────────────────────────────────────────────────────────────

class TestTriggerConfig:
    def test_trigger_byte_is_byte(self):
        assert 0 <= TRIGGER_BYTE <= 255

    def test_reset_byte_is_zero(self):
        assert RESET_BYTE == 0x00

    def test_pulse_duration_positive(self):
        assert PULSE_S > 0


# ── RTBox ─────────────────────────────────────────────────────────────────────

class TestRTBoxConfig:
    def test_event_map_has_four_buttons(self):
        btn_names = [v[0] for v in RTBOX_EVENT_MAP.values()]
        assert "1" in btn_names
        assert "2" in btn_names
        assert "3" in btn_names
        assert "4" in btn_names

    def test_event_map_ttl_values_are_powers_of_two(self):
        ttl_values = [v[1] for v in RTBOX_EVENT_MAP.values()
                      if v[0] != "light"]
        for ttl in ttl_values:
            assert ttl > 0 and (ttl & (ttl - 1)) == 0, \
                f"TTL value {ttl} is not a power of two"

    def test_clock_hz_positive(self):
        assert RTBOX_CLOCK_HZ > 0

    def test_enable_mask_is_byte(self):
        assert 0 <= RTBOX_ENABLE <= 255


# ── Stroop ────────────────────────────────────────────────────────────────────

class TestStroopConfig:
    def test_fix_range(self):
        assert 0 < FIX_MIN < FIX_MAX

    def test_incongruent_stimuli_all_different(self):
        for word, ink in INCONGRUENT_STIMULI:
            assert word != ink, f"({word}, {ink}) is not incongruent"

    def test_incongruent_stimuli_colors_defined(self):
        for word, ink in INCONGRUENT_STIMULI:
            assert word in COLORS_RGB
            assert ink in COLORS_RGB

    def test_colors_are_valid_rgb(self):
        for name, rgb in COLORS_RGB.items():
            assert len(rgb) == 3, f"{name} RGB tuple has wrong length"
            assert all(0 <= c <= 255 for c in rgb), \
                f"{name} RGB values out of range"

    def test_n_trials_covered_by_stimuli(self):
        assert N_TRIALS <= len(INCONGRUENT_STIMULI) * 10  # pool is large enough


# ── UI colours ────────────────────────────────────────────────────────────────

class TestUIColours:
    def test_colours_are_valid_rgb(self):
        for colour in (C_BG, C_WHITE, C_LAVENDER):
            assert len(colour) == 3
            assert all(0 <= c <= 255 for c in colour)
