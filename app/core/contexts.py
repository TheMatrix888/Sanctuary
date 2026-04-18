from dataclasses import dataclass
from typing import Callable, Any

from engine.screen_objects import ScreenObject
from .input_handler import InputHandler


@dataclass(frozen=True, slots=True)
class ScreenContext:
    columns: int
    lines: int
    draw: Callable[[ScreenObject], None]
    place: Callable[[ScreenObject, str], None]


@dataclass(frozen=True, slots=True)
class StateContext:
    input_handler: InputHandler
    screen_context: ScreenContext
    set_status: Callable[[str], None]
    pop_state: Callable[[], None]


@dataclass(frozen=True, slots=True)
class NavigationContext(StateContext):
    push_state: Callable[[Any], None]
    push_state_factory: Callable[[Any], None]
    stop: Callable[[], None]
