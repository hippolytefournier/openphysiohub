"""
stroop.py
─────────
Stroop colour-word task (pygame + EyeLink).

BIOPAC acquisition and matplotlib run in the main thread (see main.py).
This module only owns the pygame event loop and EyeLink sample pumping.

Public API
──────────
    run_stroop(win, F, el, cal_value, experiment_t0)
        Run the full task; return (stroop_events, gaze_samples).
"""

import time
import random
import threading

import pylink
import pygame
from pygame.locals import KEYDOWN, K_RETURN, K_ESCAPE, K_v, K_b, K_n

from .config import (
    SCREEN_W, SCREEN_H,
    C_BG, C_WHITE, C_MUTED,
    N_BLOCKS, N_TRIALS,
    FIX_MIN, FIX_MAX,
    INCONGRUENT_STIMULI, COLORS_RGB,
)
from .trigger import send_trigger
from .rtbox import rtbox_pop_events

# pygame key → response label  (defined here where pygame is already imported)
_RESP_KEYS = {K_v: "v", K_b: "b", K_n: "n"}


# ═══════════════════════════════════════════════════════════════════════════════

def run_stroop(
    win,
    F: dict,
    el: pylink.EyeLink,
    cal_value: float,
    experiment_t0: float,
) -> tuple[list, list]:
    """
    Run the Stroop task.

    Parameters
    ----------
    win            : pygame display surface
    F              : font dict (keys: title, instr, hint)
    el             : connected EyeLink instance
    cal_value      : EDA cal offset (unused here, kept for signature symmetry)
    experiment_t0  : perf_counter reference time for the session

    Returns
    -------
    (stroop_events, gaze_samples)
    """
    CX = SCREEN_W // 2
    CY = SCREEN_H // 2

    clock    = pygame.time.Clock()
    _missing = pylink.MISSING_DATA
    _stype   = pylink.SAMPLE_TYPE

    stroop_events: list[dict] = []
    gaze_samples:  list[dict] = []

    # ── Helpers ───────────────────────────────────────────────────────────────

    def log_event(name: str, **kw):
        entry = {"event": name, "t": time.perf_counter() - experiment_t0}
        entry.update(kw)
        stroop_events.append(entry)
        el.sendMessage(f"STROOP_{name.upper()}")

    def pump_eyelink():
        """Drain all available EyeLink samples from the link queue."""
        while True:
            dt = el.getNextData()
            if dt != _stype:
                break
            s = el.getFloatData()
            if s is None:
                break
            ts = s.getTime()
            le = s.isLeftSample()
            re = s.isRightSample()
            gx = gy = pa = None
            if le:
                gx, gy = s.getLeftEye().getGaze()
                pa     = s.getLeftEye().getPupilSize()
            elif re:
                gx, gy = s.getRightEye().getGaze()
                pa     = s.getRightEye().getPupilSize()
            gaze_samples.append({
                "t":          ts,
                "wall_t":     round(time.perf_counter() - experiment_t0, 4),
                "eye":        "left" if le else "right",
                "gaze_x":     round(gx, 2) if gx not in (None, _missing) else "NA",
                "gaze_y":     round(gy, 2) if gy not in (None, _missing) else "NA",
                "pupil_size": round(pa, 2) if pa not in (None, _missing, 0.0) else "NA",
                # Bit mapping validated experimentally (EyeLink bits → RTBox)
                "button1": (s.getButtons() >> 6) & 1,   # b6  TTL 64
                "button2": (s.getButtons() >> 5) & 1,   # b5  TTL 32
                "button3": (s.getButtons() >> 4) & 1,   # b4  TTL 16
                "button4": (s.getButtons() >> 3) & 1,   # b3  TTL 8
                "light":   (s.getButtons() >> 1) & 1,   # b1  TTL 2
            })

    def make_block() -> list:
        pool = INCONGRUENT_STIMULI * (N_TRIALS // len(INCONGRUENT_STIMULI) + 1)
        return random.sample(pool, N_TRIALS)

    # ── Instruction screen ────────────────────────────────────────────────────
    try:
        win.fill(C_BG)
        msg1 = F["title"].render("Tâche Stroop", True, C_WHITE)
        msg2 = F["instr"].render(
            "Appuyez sur V, B ou N selon la COULEUR du mot.", True, C_MUTED)
        msg3 = F["hint"].render(
            "Appuyez sur ENTREE pour commencer.", True, C_MUTED)
        win.blit(msg1, (CX - msg1.get_width() // 2, CY - 120))
        win.blit(msg2, (CX - msg2.get_width() // 2, CY - 40))
        win.blit(msg3, (CX - msg3.get_width() // 2, CY + 40))
        pygame.display.flip()

        waiting = True
        while waiting:
            pump_eyelink()
            for ev in pygame.event.get():
                if ev.type == KEYDOWN and ev.key == K_RETURN:
                    waiting = False
            clock.tick(60)

        # ── Blocks ────────────────────────────────────────────────────────────
        for bloc_n in range(1, N_BLOCKS + 1):
            log_event("bloc_start", bloc=bloc_n)
            trials = make_block()

            for trial_n, (word, ink_color) in enumerate(trials, 1):

                # Fixation cross
                fix_dur = random.uniform(FIX_MIN, FIX_MAX)
                win.fill(C_BG)
                pygame.draw.rect(win, C_WHITE, pygame.Rect(CX - 20, CY - 2,  40, 4))
                pygame.draw.rect(win, C_WHITE, pygame.Rect(CX - 2,  CY - 20,  4, 40))
                pygame.display.flip()

                threading.Thread(target=send_trigger, args=(1,), daemon=True).start()
                log_event("fixation_on", bloc=bloc_n, trial=trial_n,
                          word=word, ink=ink_color, duration=round(fix_dur, 4))

                fix_end = time.perf_counter() + fix_dur
                while time.perf_counter() < fix_end:
                    pump_eyelink()
                    for ev in pygame.event.get():
                        if ev.type == KEYDOWN and ev.key == K_ESCAPE:
                            return stroop_events, gaze_samples
                    clock.tick(200)

                # Word stimulus
                win.fill(C_BG)
                word_surf = F["title"].render(word, True, COLORS_RGB[ink_color])
                win.blit(word_surf, (
                    CX - word_surf.get_width()  // 2,
                    CY - word_surf.get_height() // 2,
                ))
                pygame.display.flip()

                threading.Thread(target=send_trigger, args=(2,), daemon=True).start()
                log_event("word_on", bloc=bloc_n, trial=trial_n,
                          word=word, ink=ink_color)

                response  = None
                rt_start  = time.perf_counter()
                while response is None:
                    pump_eyelink()

                    # RTBox buttons (TTL already sent by the serial thread)
                    for ev in rtbox_pop_events():
                        rt_s = ev["host_t"] - rt_start
                        log_event("rtbox_button", bloc=bloc_n, trial=trial_n,
                                  word=word, ink=ink_color,
                                  btn=ev["btn"], ttl=ev["ttl"],
                                  rt_s=round(rt_s, 4),
                                  box_secs=round(ev["box_secs"], 4))
                        if response is None:
                            response = f"rtbox_{ev['btn']}"

                    # Keyboard fallback
                    for ev in pygame.event.get():
                        if ev.type == KEYDOWN:
                            if ev.key in _RESP_KEYS:
                                response = _RESP_KEYS[ev.key]
                            elif ev.key == K_ESCAPE:
                                return stroop_events, gaze_samples
                    clock.tick(200)

                log_event("response", bloc=bloc_n, trial=trial_n,
                          word=word, ink=ink_color,
                          key=response,
                          source="rtbox" if str(response).startswith("rtbox_") else "keyboard",
                          rt_s=round(time.perf_counter() - rt_start, 4))

            log_event("bloc_end", bloc=bloc_n)

            if bloc_n < N_BLOCKS:
                win.fill(C_BG)
                pause_msg = F["instr"].render(
                    f"Fin du bloc {bloc_n}/{N_BLOCKS}. Appuyez sur ENTREE pour continuer.",
                    True, C_WHITE)
                win.blit(pause_msg, (CX - pause_msg.get_width() // 2, CY - 30))
                pygame.display.flip()
                waiting = True
                while waiting:
                    pump_eyelink()
                    for ev in pygame.event.get():
                        if ev.type == KEYDOWN and ev.key == K_RETURN:
                            waiting = False
                    clock.tick(60)

        # ── End screen ────────────────────────────────────────────────────────
        win.fill(C_BG)
        end_msg = F["title"].render("Terminé. Merci !", True, C_WHITE)
        sub_msg = F["instr"].render("Fermeture en cours…",  True, C_MUTED)
        win.blit(end_msg, (CX - end_msg.get_width() // 2, CY - 40))
        win.blit(sub_msg, (CX - sub_msg.get_width() // 2, CY + 20))
        pygame.display.flip()

        t_end = time.perf_counter()
        while (time.perf_counter() - t_end) < 2.0:
            pump_eyelink()
            for ev in pygame.event.get():
                if ev.type in (pygame.QUIT, KEYDOWN):
                    break
            clock.tick(60)

    finally:
        pass   # BIOPAC teardown is handled in main()

    return stroop_events, gaze_samples
