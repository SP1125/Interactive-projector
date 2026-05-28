# game_loop.py

import queue as _queue
import pygame

from queue_bus import event_queue
from events import EventType, GameEvent
from modes.base import GameMode
from modes.draw_mode import DrawMode

# ── ADD NEW MODES HERE ────────────────────────────────────────────────────────
from modes.battleships import BattleshipsMode
# from modes.your_mode import YourMode
# ─────────────────────────────────────────────────────────────────────────────

_FPS = 60
_WINDOW_W = 1280
_WINDOW_H = 720


def run_game() -> None:
    pygame.init()
    screen = pygame.display.set_mode((_WINDOW_W, _WINDOW_H), pygame.FULLSCREEN)
    pygame.display.set_caption("T7")
    clock = pygame.time.Clock()

    # ── STARTING MODE — change this to swap the entry screen ─────────────────
    active_mode: GameMode = DrawMode()
    # ─────────────────────────────────────────────────────────────────────────

    running = True

    while running:

        # ── 1. Drain vision events ────────────────────────────────────────────
        while True:
            try:
                event = event_queue.get_nowait()
                result = active_mode.handle_event(event)
                # If handle_event returns a new GameMode instance, switch to it.
                # Game/UI team: return a mode instance from handle_event to trigger a switch.
                # e.g. return MenuMode() from inside your mode to transition.
                if isinstance(result, GameMode):
                    active_mode = result
            except _queue.Empty:
                break

        # ── 2. Pygame OS events ───────────────────────────────────────────────
        for pg_event in pygame.event.get():
            if pg_event.type == pygame.QUIT:
                running = False
            elif pg_event.type == pygame.KEYDOWN:
                if pg_event.key == pygame.K_ESCAPE:
                    running = False
                elif pg_event.key == pygame.K_SPACE:
                    mx, my = pygame.mouse.get_pos()
                    active_mode.handle_event(
                        GameEvent(EventType.TAP, {"x": mx, "y": my})
                    )

        # ── Mouse as stand-in for vision events (remove once CV team integrates)
        mouse_buttons = pygame.mouse.get_pressed()
        mx, my = pygame.mouse.get_pos()
        if mouse_buttons[0]:
            active_mode.handle_event(GameEvent(EventType.DRAG, {"x": mx, "y": my}))
        else:
            active_mode.handle_event(GameEvent(EventType.RELEASE, {"x": mx, "y": my}))

        # ── 3. Update ─────────────────────────────────────────────────────────
        active_mode.update()

        # ── 4. Render ─────────────────────────────────────────────────────────
        active_mode.render(screen)
        pygame.display.flip()

        # ── 5. Cap to 60 FPS ──────────────────────────────────────────────────
        clock.tick(_FPS)

    pygame.quit()