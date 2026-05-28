from dataclasses import dataclass, field
from enum import Enum, auto
import time


class EventType(Enum):
    TAP = auto()       # finger touched down
    RELEASE = auto()   # finger lifted
    DRAG = auto()      # finger moving while down


@dataclass
class GameEvent:
    type: EventType
    payload: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    # payload examples:
    #   TAP/RELEASE/DRAG: {"x": 320, "y": 240, "hand": "right"}