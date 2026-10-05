"""
Platform factory and subsystem bootstrap for Sanctuary.
Provides unified platform hardware bundle encapsulation (terminal, clock, input).
"""
import sys
from dataclasses import dataclass

from sanctuary.core.clock import WindowsClock, Clock
from sanctuary.core.input_handler import InputHandler, WindowsInputHandler, VirtualInputHandler
from sanctuary.core.terminal import Terminal, WindowsTerminal, VirtualTerminal


@dataclass(slots=True, frozen=True)
class Platform:
    terminal: Terminal
    clock: Clock
    input_handler: InputHandler


def detect_platform() -> str:
    """Autodetects the host system platform."""
    if sys.platform == "win32":
        return "windows"
    return "virtual"


def create_platform(platform_name: str = "auto") -> Platform:
    """
    Creates and returns a concrete Platform instance.
    Defaults to 'auto', which autodetects Windows or virtual fallback.
    """
    resolved_name = detect_platform() if platform_name == "auto" else platform_name.lower()

    if resolved_name == "windows":
        terminal = WindowsTerminal()
        return Platform(
            terminal=terminal,
            clock=WindowsClock(),
            input_handler=WindowsInputHandler(terminal),
        )
    elif resolved_name == "virtual":
        return Platform(
            terminal=VirtualTerminal(),
            clock=Clock(),
            input_handler=VirtualInputHandler(),
        )
    raise ValueError(f"Platform '{platform_name}' (resolved as '{resolved_name}') not supported")
