#draw_mode.py

import pygame
from events import EventType, GameEvent
from modes.base import GameMode

_BG = (255, 255, 255)
_BRUSH_COLOR = (0, 0, 0)
_BRUSH_RADIUS = 8


class DrawMode(GameMode):
    """
    Test mode: draws circles wherever a TAP or DRAG event lands.
    Lets you verify the full pipeline is working before adding real game logic.

    TAP   → single dot at the touch point
    DRAG  → continuous line as finger moves
    RELEASE → lifts the pen (resets drag state)
    """

    def __init__(self) -> None:
        self._canvas: pygame.Surface | None = None  # created lazily on first render
        self._drawing = False
        self._last_pos: tuple[int, int] | None = None

    def handle_event(self, event: GameEvent) -> None:
        x = event.payload.get("x", 0)
        y = event.payload.get("y", 0)

        if event.type == EventType.TAP:
            self._drawing = True
            self._last_pos = (x, y)
            if self._canvas:
                pygame.draw.circle(self._canvas, _BRUSH_COLOR, (x, y), _BRUSH_RADIUS)

        elif event.type == EventType.DRAG:
            self._drawing = True
            if self._canvas and self._last_pos:
                # Draw a line from last known position to current — smooth stroke
                pygame.draw.line(self._canvas, _BRUSH_COLOR, self._last_pos, (x, y), _BRUSH_RADIUS * 2)
                pygame.draw.circle(self._canvas, _BRUSH_COLOR, (x, y), _BRUSH_RADIUS)
            self._last_pos = (x, y)

        elif event.type == EventType.RELEASE:
            self._drawing = False
            self._last_pos = None

    def update(self) -> None:
        pass  # nothing to update between events in this mode

    def render(self, surface: pygame.Surface) -> None:
        if self._canvas is None:
            self._canvas = pygame.Surface(surface.get_size())
            self._canvas.fill(_BG)
        
        # Always blit the full canvas — this is the persistent drawing surface
        surface.blit(self._canvas, (0, 0))

        # Cursor ring on top
        if self._drawing and self._last_pos:
            pygame.draw.circle(surface, (255, 255, 255), self._last_pos, _BRUSH_RADIUS + 4, 2)