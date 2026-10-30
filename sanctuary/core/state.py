"""
Application state and Command pattern primitives for Sanctuary.
Provides the base State lifecycle contract and modal transition commands.
"""
from __future__ import annotations

from dataclasses import dataclass
from multiprocessing import Process

from sanctuary.core.geometry import Size
from sanctuary.core.input_handler import InputHandler, Key
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


@dataclass(slots=True, frozen=True)
class ToggleMetrics(Command):
    """Toggles global runtime performance metrics and telemetry overlay."""
    pass


@dataclass(slots=True, frozen=True)
class Batch(Command):
    """Executes a composite sequence of state transition and lifecycle commands atomically."""
    commands: tuple[Command, ...]

    def __init__(self, *commands: Command) -> None:
        object.__setattr__(self, "commands", tuple(commands))


@dataclass(slots=True, frozen=True)
class StartProcess(Command):
    """Spawns an operating system background process and registers it in the application supervisor."""
    process: Process


@dataclass(slots=True, frozen=True)
class TerminateProcess(Command):
    """Terminates an operating system background process by name and unregisters it from application tracking."""
    name: str


class State:
    """
    Abstract base lifecycle contract for Sanctuary states and scenes.
    """

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        """Processes input events and optionally dispatches a lifecycle command."""
        if input_handler.just_pressed(Key.F3):
            return ToggleMetrics()
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
