from dataclasses import dataclass
from typing import Callable, Any

from .input_handler import InputHandler
from engine.screen import Screen


@dataclass(frozen=True, slots=True)
class StateContext:
    input_handler: InputHandler
    screen: Screen
    set_status: Callable[[str], None]
    pop_state: Callable[[], None]


@dataclass(frozen=True, slots=True)
class MenuContext(StateContext):
    push_state: Callable[[Any], None]
    push_state_factory: Callable[[Any], None]
    stop: Callable[[], None]
