# base.py

import pygame
from events import GameEvent
from input_state import InputState


class GameMode:
    """
    Base class for all game modes (screens/states).
    Subclass this and override the three methods below.
    """

    def handle_event(self, event: GameEvent) -> None:
        """Called for every event drained from the queue this frame."""
        pass

    def update(self, input_state: InputState) -> None:
        """Called once per frame for any state changes not driven by events."""
        pass

    def render(self, surface: pygame.Surface, input_state: InputState) -> None:
        """Called once per frame. Draw everything onto `surface`."""
        pass