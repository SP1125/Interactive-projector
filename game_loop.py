# game_loop.py

import sys
import queue
import threading
import traceback
import faulthandler

import pygame

from queue_bus import event_queue
from events import EventType, GameEvent
from modes.base import GameMode
from input_state import InputState
from vision_thread import main as vision_main

# ── ADD NEW MODES HERE ────────────────────────────────────────────────────────
from modes.battleships.battleships_mode import BattleshipsMode
# from modes.your_mode import YourMode
# ─────────────────────────────────────────────────────────────────────────────

_FPS = 60
_WINDOW_W = 1280
_WINDOW_H = 720
USE_VISION_INPUT = True

def run_game() -> None:
    faulthandler.enable()
    threading.Thread(target=vision_main, daemon=True).start()

    pygame.init()
    screen = pygame.display.set_mode((_WINDOW_W, _WINDOW_H), pygame.FULLSCREEN)
    pygame.display.set_caption("T7")
    clock = pygame.time.Clock()
    input_state = InputState()

    # ── STARTING MODE — change this to swap the entry screen ─────────────────
    active_mode: GameMode = BattleshipsMode()
    # ─────────────────────────────────────────────────────────────────────────

    running = True

    try:
        while running:
            try:

                # ── 1. Drain vision events ───────────────────────────────────────────
                while True:
                    try:
                        event = event_queue.get_nowait()
                        print(f"[GAME LOOP] got event: {event.type} payload: {event.payload}")
                    except queue.Empty:
                        break

                    if event.type == EventType.TAP:
                        input_state.x = event.payload["x"]
                        input_state.y = event.payload["y"]
                        input_state.tapping = True
                    elif event.type == EventType.DRAG:
                        input_state.x = event.payload["x"]
                        input_state.y = event.payload["y"]
                        input_state.dragging = True
                    elif event.type == EventType.RELEASE:
                        input_state.tapping = False
                        input_state.dragging = False

                    result = active_mode.handle_event(event)
                    if isinstance(result, GameMode):
                        active_mode = result

                # ── 2. Pygame OS events ──────────────────────────────────────────────
                for pg_event in pygame.event.get():
                    if pg_event.type == pygame.QUIT:
                        running = False
                    elif pg_event.type == pygame.KEYDOWN:
                        if pg_event.key == pygame.K_ESCAPE:
                            running = False
                        elif pg_event.key == pygame.K_SPACE:
                            mx, my = pygame.mouse.get_pos()
                            result = active_mode.handle_event(
                                GameEvent(EventType.TAP, {"x": mx, "y": my})
                            )
                            if isinstance(result, GameMode):
                                active_mode = result

                # ── Mouse fallback (disable once CV is stable) ────────────────────────
                if not USE_VISION_INPUT:
                    mx, my = pygame.mouse.get_pos()
                    btn = pygame.mouse.get_pressed()[0]
                    event_type = EventType.DRAG if btn else EventType.RELEASE
                    result = active_mode.handle_event(GameEvent(event_type, {"x": mx, "y": my}))
                    if isinstance(result, GameMode):
                        active_mode = result

                # ── 3. Update ────────────────────────────────────────────────────────
                active_mode.update(input_state)

                # ── 4. Render ────────────────────────────────────────────────────────
                active_mode.render(screen, input_state)
                pygame.display.flip()

                # ── 5. Cap to 60 FPS ─────────────────────────────────────────────────
                clock.tick(_FPS)

            except Exception:
                traceback.print_exc()
                running = False

    finally:
        pygame.quit()
        sys.exit()