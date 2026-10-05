"""
Application state and Command pattern primitives for Sanctuary.
Provides the base State lifecycle contract and modal transition commands.
"""
from __future__ import annotations

from dataclasses import dataclass

from sanctuary.core.geometry import Size
from sanctuary.core.input_handler import InputHandler
from sanctuary.core.screen import Screen


class Command:
    """Base class for state lifecycle transition commands."""
    pass


@dataclass(slots=True, frozen=True)
class Push(Command):
    """Pushes a new state onto the top of the state stack."""
    state: State


@dataclass(slots=True, frozen=True)
class Change(Command):
    """Replaces the active state on the top of the stack with a new state."""
    state: State


@dataclass(slots=True, frozen=True)
class Pop(Command):
    """Pops the active state from the top of the stack."""
    pass


@dataclass(slots=True, frozen=True)
class Quit(Command):
    """Terminates the application main loop."""
    pass


class State:
    """
    Abstract base lifecycle contract for Sanctuary states and scenes.
    """

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        """Processes input events and optionally dispatches a lifecycle command."""
        return None

    def update(self, dt: float, screen_size: Size) -> None:
        """Executes per-frame simulation physics and layout logic."""
        pass

    def draw(self, screen: Screen) -> None:
        """Renders state graphics onto the Screen double buffer."""
        pass

    def on_enter(self) -> None:
        """Lifecycle hook invoked when state is activated or pushed onto the stack."""
        pass

    def on_exit(self) -> None:
        """Lifecycle hook invoked when state is popped or terminated."""
        pass
