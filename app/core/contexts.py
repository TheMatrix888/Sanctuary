from dataclasses import dataclass
from typing import Callable, Any

from engine.primitives import Size
from engine.screen.objects import ScreenObject
from app.input import InputHandler


@dataclass(frozen=True, slots=True)
class ScreenContext:
    size: Size
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
