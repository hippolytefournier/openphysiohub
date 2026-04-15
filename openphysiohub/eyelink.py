"""
eyelink.py
──────────
EyeLink eye-tracker connection, configuration, and calibration UI.

sys.path is extended here so CalibrationGraphicsPygame can be imported;
os.chdir is NOT called here — main() sets the working directory to
LIB_ET_DIR before creating CalibrationGraphics so the sound files are
found via relative paths.

Public API
──────────
    connect_eyelink()                   connect + configure the tracker
    run_eyelink_calibration(el, win, F) pygame calibration menu
    DummyDisplay                        no-op EyeLinkCustomDisplay subclass
"""

import sys
import math
import time

import pylink
import pygame
from pygame.locals import (
    QUIT, KEYDOWN, MOUSEBUTTONDOWN,
    K_RETURN, K_DOWN, K_UP, K_ESCAPE,
    KMOD_LCTRL, KMOD_RCTRL,
)

from .config import (
    LIB_ET_DIR,
    DUMMY_MODE,
    SCREEN_W, SCREEN_H,
    EYELINK_IP,
    C_BG, C_BORDER, C_ACCENT, C_ACCENT_LT,
    C_LAVENDER, C_MUTED, C_WHITE,
    C_DISABLED, C_DISABLED_T,
    C_DONE_BG, C_DONE_FG,
)

# Make CalibrationGraphicsPygame importable
if str(LIB_ET_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_ET_DIR))

from CalibrationGraphicsPygame import CalibrationGraphics  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════════════
#  DummyDisplay
# ═══════════════════════════════════════════════════════════════════════════════

class DummyDisplay(pylink.EyeLinkCustomDisplay):
    """No-op display used to keep pylink active after calibration closes."""
    def setup_cal_display(self):             pass
    def exit_cal_display(self):              pass
    def record_abort_hide(self):             pass
    def clear_cal_display(self):             pass
    def erase_cal_target(self):              pass
    def draw_cal_target(self, x, y):         pass
    def play_beep(self, beepid):             pass
    def get_mouse_state(self):               return (0, 0), 0
    def get_input_key(self):                 return []
    def exit_image_display(self):            pass
    def alert_printf(self, msg):             print("EyeLink:", msg)
    def setup_image_display(self, w, h):     pass
    def image_title(self, text):             pass
    def draw_image_line(self, w, line, tot, buff): pass
    def set_image_palette(self, r, g, b):    pass
    def draw_line(self, x1, y1, x2, y2, colorindex): pass
    def draw_lozenge(self, x, y, w, h, colorindex):   pass


# ═══════════════════════════════════════════════════════════════════════════════
#  Connection & configuration
# ═══════════════════════════════════════════════════════════════════════════════

def connect_eyelink() -> pylink.EyeLink:
    """Connect to the tracker, open the EDF file, and apply recording settings."""
    if DUMMY_MODE:
        el = pylink.EyeLink(None)
    else:
        try:
            el = pylink.EyeLink(EYELINK_IP)
        except RuntimeError as e:
            print("Connexion EyeLink impossible :", e)
            sys.exit(1)

    print("[ET] EyeLink connecté")
    el.openDataFile("calib.edf")
    el.sendCommand("add_file_preamble_text 'EXPERIMENT'")
    el.setOfflineMode()
    el.sendCommand(f"screen_pixel_coords = 0 0 {SCREEN_W-1} {SCREEN_H-1}")
    el.sendMessage(f"DISPLAY_COORDS 0 0 {SCREEN_W-1} {SCREEN_H-1}")
    el.sendCommand("sample_rate = 1000")
    el.sendCommand("recording_parse_type = GAZE")
    el.sendCommand("select_parser_configuration = 0")
    el.sendCommand("binocular_enabled = NO")
    el.sendCommand("calibration_type = HV9")
    el.sendCommand("link_sample_data = LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,BUTTON")
    el.sendCommand("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON")
    el.sendCommand("file_sample_data = LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,BUTTON")
    return el


# ═══════════════════════════════════════════════════════════════════════════════
#  Calibration UI
# ═══════════════════════════════════════════════════════════════════════════════

def run_eyelink_calibration(el: pylink.EyeLink, win, F: dict) -> dict:
    """
    Run the pygame calibration menu (calibrate → validate → ready to record).

    Returns
    -------
    dict with keys "calibration" and "validation", each holding the result
    dict collected from the tracker firmware, or None if skipped.
    """
    CX = SCREEN_W // 2
    CY = SCREEN_H // 2
    BW, BH, GAP = 430, 58, 20

    calib_info = {"calibration": None, "validation": None}

    # ── Helpers ──────────────────────────────────────────────────────────────

    def draw_background():
        win.fill(C_BG)
        dot = (30, 32, 34)
        for x in range(0, SCREEN_W + 40, 40):
            for y in range(0, SCREEN_H + 40, 40):
                pygame.draw.circle(win, dot, (x, y), 1)

    def quit_app():
        el.close()
        pygame.quit()
        sys.exit()

    def check_quit(event):
        if event.type == QUIT:
            quit_app()
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                quit_app()
            if event.key in (pygame.K_c,) and event.mod in [
                KMOD_LCTRL, KMOD_RCTRL, 4160, 4224
            ]:
                quit_app()

    def instruction_screen(txt: str):
        clock = pygame.time.Clock()
        while True:
            draw_background()
            msg  = F["instr"].render(txt, True, C_WHITE)
            hint = F["hint"].render("Appuyer sur Entrée pour continuer", True, C_MUTED)
            win.blit(msg,  (CX - msg.get_width()  // 2, CY - 60))
            win.blit(hint, (CX - hint.get_width() // 2, CY + 20))
            pygame.display.flip()
            for event in pygame.event.get():
                check_quit(event)
                if event.type == KEYDOWN and event.key == K_RETURN:
                    return
            clock.tick(60)

    # ── Click-to-focus screen ─────────────────────────────────────────────────
    clock = pygame.time.Clock()
    t = 0
    while True:
        t += 1
        draw_background()
        pulse = 1.0 + 0.05 * math.sin(t * 0.05)
        er    = int(38 * pulse)
        ey    = CY - 200
        halo  = pygame.Surface((er * 6, er * 6), pygame.SRCALPHA)
        ha    = int(22 + 18 * math.sin(t * 0.06))
        pygame.draw.circle(halo, (*C_ACCENT, ha), (er * 3, er * 3), er * 2)
        win.blit(halo, (CX - er * 3, ey - er * 3))
        pygame.draw.circle(win, C_ACCENT, (CX, ey), er)
        pygame.draw.circle(win, C_BG,     (CX, ey), er // 3)
        label = F["title"].render("Cliquer pour commencer", True, C_WHITE)
        win.blit(label, (CX - label.get_width() // 2, CY - 30))
        pygame.display.flip()
        clicked = False
        for event in pygame.event.get():
            check_quit(event)
            if event.type == MOUSEBUTTONDOWN:
                clicked = True
        if clicked:
            break
        clock.tick(60)

    # ── Calibration result collection ─────────────────────────────────────────

    def collect_calib_result(phase: str):
        result = {"timestamp": time.strftime("%H:%M:%S"), "phase": phase}
        try:
            pylink.msecDelay(200)
            msg = el.getCalibrationMessage()
            if msg:
                msg = msg.strip()
                result["raw_message"] = msg
                if phase == "calibration":
                    if msg.startswith("calibration_result:"):
                        result["cal_result"] = msg.split(":", 1)[1].strip()
                elif phase == "validation":
                    if msg.startswith("validation_result:"):
                        parts = msg.split(":", 1)[1].strip().split()
                        if len(parts) >= 1: result["avg_error"] = parts[0]
                        if len(parts) >= 2: result["max_error"] = parts[1]
                        if len(parts) >= 4:
                            result["offset_x"] = parts[2]
                            result["offset_y"] = parts[3]
        except Exception as e:
            result["parse_error"] = str(e)
        calib_info[phase] = result
        print(f"  [{phase}] {result}")

    def do_tracker_setup(phase: str):
        pygame.event.set_grab(False)
        win.fill(C_BG)
        pygame.display.flip()
        pylink.pumpDelay(100)
        try:
            el.doTrackerSetup()
        except RuntimeError as err:
            print("ERROR:", err)
            el.exitCalibration()
        collect_calib_result(phase)

    # ── Button menu ───────────────────────────────────────────────────────────
    n_btns  = 3
    total_h = n_btns * BH + (n_btns - 1) * GAP
    y0      = CY - total_h // 2 + 20

    btns = [
        {"label": "Calibration",      "c_idle": C_ACCENT,    "c_focus": C_ACCENT_LT, "enabled": True,  "done": False},
        {"label": "Validation",       "c_idle": C_ACCENT,    "c_focus": C_ACCENT_LT, "enabled": False, "done": False},
        {"label": "Lancer le record", "c_idle": (50, 52, 64), "c_focus": (68, 70, 86), "enabled": False, "done": False},
    ]
    cursor = 0
    t = 0

    def draw_btn(idx: int):
        b       = btns[idx]
        focused = (idx == cursor)
        x    = CX - BW // 2
        y    = y0 + idx * (BH + GAP)
        rect = pygame.Rect(x, y, BW, BH)
        if not b["enabled"]:
            bg, tc, bc, bw_ = C_DISABLED, C_DISABLED_T, C_BORDER, 1
        elif focused:
            bg, tc, bc, bw_ = b["c_focus"], C_BG, C_LAVENDER, 2
        else:
            bg, tc, bc, bw_ = b["c_idle"], C_BG, (0, 0, 0), 0
        if focused and b["enabled"]:
            ga = int(28 + 16 * math.sin(t * 0.08))
            gs = pygame.Surface((BW + 26, BH + 26), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*b["c_focus"], ga), (0, 0, BW + 26, BH + 26), border_radius=20)
            win.blit(gs, (x - 13, y - 13))
        pygame.draw.rect(win, bg, rect, border_radius=14)
        if bw_:
            pygame.draw.rect(win, bc, rect, bw_, border_radius=14)
        num = F["tag"].render(str(idx + 1), True, C_LAVENDER if b["enabled"] else C_DISABLED_T)
        win.blit(num, (x + 20, y + BH // 2 - num.get_height() // 2))
        lbl = F["btn"].render(b["label"], True, tc if b["enabled"] else C_DISABLED_T)
        win.blit(lbl, (x + 52, y + BH // 2 - lbl.get_height() // 2))
        if b["done"]:
            ok  = F["badge"].render("OK", True, C_DONE_FG)
            ow  = ok.get_width() + 18
            oh  = ok.get_height() + 8
            or_ = pygame.Rect(x + BW - ow - 16, y + BH // 2 - oh // 2, ow, oh)
            pygame.draw.rect(win, C_DONE_BG, or_, border_radius=oh // 2)
            pygame.draw.rect(win, C_ACCENT,  or_, 1, border_radius=oh // 2)
            win.blit(ok, (or_.x + 9, or_.y + 4))

    while True:
        t += 1
        draw_background()
        header_y = y0 - 130
        title = F["title"].render("EyeLink  Setup", True, C_WHITE)
        win.blit(title, (CX - title.get_width() // 2, header_y))
        sub = F["sub"].render("Calibration & validation avant le recording", True, C_MUTED)
        win.blit(sub, (CX - sub.get_width() // 2, header_y + 52))
        pygame.draw.line(win, C_BORDER, (CX - 220, header_y + 80), (CX + 220, header_y + 80), 1)
        for i in range(len(btns)):
            draw_btn(i)
        nav = F["hint"].render(
            "Fleche haut/bas  naviguer    Entree  selectionner    Ctrl-C  quitter",
            True, C_MUTED)
        win.blit(nav, (CX - nav.get_width() // 2, SCREEN_H - 50))
        pygame.display.flip()

        active = [i for i, b in enumerate(btns) if b["enabled"]]
        for event in pygame.event.get():
            check_quit(event)
            if event.type == KEYDOWN:
                if event.key == K_DOWN:
                    pos    = active.index(cursor) if cursor in active else 0
                    cursor = active[(pos + 1) % len(active)]
                if event.key == K_UP:
                    pos    = active.index(cursor) if cursor in active else 0
                    cursor = active[(pos - 1) % len(active)]
                if event.key == K_RETURN:
                    if cursor == 0 and btns[0]["enabled"]:
                        instruction_screen("Appuyer sur C pour demarrer la calibration")
                        if not DUMMY_MODE:
                            do_tracker_setup("calibration")
                        btns[0]["done"]    = True
                        btns[1]["enabled"] = True
                        cursor = 1
                    elif cursor == 1 and btns[1]["enabled"]:
                        instruction_screen("Appuyer sur V pour demarrer la validation")
                        if not DUMMY_MODE:
                            do_tracker_setup("validation")
                        btns[1]["done"]    = True
                        btns[2]["enabled"] = True
                        cursor = 2
                    elif cursor == 2 and btns[2]["enabled"]:
                        return calib_info   # bureau visible

        clock.tick(60)
