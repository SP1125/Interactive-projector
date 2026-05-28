import pygame
from events import GameEvent


class GameMode:
    """
    Base class for all game modes (screens/states).
    Subclass this and override the three methods below.
    """

    def handle_event(self, event: GameEvent) -> None:
        """Called for every event drained from the queue this frame."""
        pass

    def update(self) -> None:
        """Called once per frame for any state changes not driven by events."""
        pass

    def render(self, surface: pygame.Surface) -> None:
        """Called once per frame. Draw everything onto `surface`."""
        pass