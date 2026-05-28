from modes.base import GameMode
from events import EventType, GameEvent
import pygame

class BattleshipsMode(GameMode):

    def __init__(self):
        # ALL game state lives here
        self.grid = [[None] * 10 for _ in range(10)]
        self.current_turn = "player1"
        self.cell_size = 60

    def handle_event(self, event: GameEvent):
        # Called for every vision/input event this frame.
        # Update your state here — don't draw anything here.
        if event.type == EventType.TAP:
            col = event.payload["x"] // self.cell_size
            row = event.payload["y"] // self.cell_size
            self.grid[row][col] = "hit" if self._is_ship(row, col) else "miss"

        # Return a GameMode instance to switch to that mode:
        # e.g. return MenuMode() transitions immediately after this frame.

    def update(self):
        # Called once per frame.
        # Use for animations, turn timers, AI moves — anything time-based.
        pass

    def render(self, surface):
        # Called 60x per second. Redraws the entire game from current state.
        # surface is a pygame.Surface the size of the window — draw onto it.
        for row in range(10):
            for col in range(10):
                color = self._cell_color(row, col)
                rect = pygame.Rect(
                    col * self.cell_size, row * self.cell_size,
                    self.cell_size, self.cell_size
                )
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (0, 0, 0), rect, 1)  # grid lines