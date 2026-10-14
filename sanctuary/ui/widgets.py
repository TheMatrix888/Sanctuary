"""
Declarative, polymorphic TUI Form widgets and controls.
Provides interactive items for numeric parameter adjustments, discrete choices, and actions.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from sanctuary.core.state import Command


class FormItem(ABC):
    """Abstract interface for interactive form and inspector rows."""
    label: str

    @abstractmethod
    def render_value(self) -> str:
        """Formatted string representation of current value to display beside the label."""
        pass

    @abstractmethod
    def on_adjust(self, delta: int, multiplier: float = 1.0) -> None:
        """Handles horizontal adjustment (Left/Right arrow keys)."""
        pass

    @abstractmethod
    def on_activate(self) -> Command | None:
        """Handles primary execution (Enter key)."""
        pass

    @abstractmethod
    def on_reset(self) -> None:
        """Restores default state/value (R key)."""
        pass

    @abstractmethod
    def get_help_hint(self) -> str:
        """Contextual navigation hint for the bottom status bar when hovered."""
        pass


@dataclass(slots=True)
class Knob(FormItem):
    """
    Numeric parameter controller with mandatory min/max bounds,
    precision formatting, Ctrl acceleration, and default value reset.
    """
    label: str
    value: float
    min_value: float
    max_value: float
    delta: float = 1.0
    precision: int = 2
    default_value: float | None = None
    suffix: str = ""

    def __post_init__(self) -> None:
        if self.default_value is None:
            self.default_value = self.value
        self.value = max(self.min_value, min(self.value, self.max_value))

    def render_value(self) -> str:
        if self.precision == 0:
            formatted = f"{int(round(self.value))}"
        else:
            formatted = f"{self.value:.{self.precision}f}"
        if self.suffix:
            return f"[{formatted} {self.suffix}]"
        return f"[{formatted}]"

    def on_adjust(self, delta: int, multiplier: float = 1.0) -> None:
        step = self.delta * delta * multiplier
        new_value = round(self.value + step, 6)
        self.value = max(self.min_value, min(new_value, self.max_value))

    def on_activate(self) -> Command | None:
        return None

    def on_reset(self) -> None:
        if self.default_value is not None:
            self.value = self.default_value

    def get_help_hint(self) -> str:
        return "[←/→] Adjust  [Ctrl+←/→] x10  [R] Reset  [Esc] Back"


@dataclass(slots=True)
class ChoiceKnob(FormItem):
    """Discrete option selector cycling through a list of string values."""
    label: str
    values: list[str]
    index: int = 0
    default_index: int | None = None

    def __post_init__(self) -> None:
        if self.default_index is None:
            self.default_index = self.index
        if self.values:
            self.index = self.index % len(self.values)

    @property
    def current_value(self) -> str:
        if 0 <= self.index < len(self.values):
            return self.values[self.index]
        return ""

    def render_value(self) -> str:
        return f"[{self.current_value}]"

    def on_adjust(self, delta: int, multiplier: float = 1.0) -> None:
        if self.values:
            self.index = (self.index + delta) % len(self.values)

    def on_activate(self) -> Command | None:
        return None

    def on_reset(self) -> None:
        if self.default_index is not None:
            self.index = self.default_index

    def get_help_hint(self) -> str:
        return "[←/→] Cycle option  [R] Reset  [Esc] Back"


@dataclass(slots=True)
class Button(FormItem):
    """Action button triggering a State Stack Command or callback on Enter."""
    label: str
    action: Command | None = None
    callback: Callable[[], Command | None] | None = None

    def render_value(self) -> str:
        return ""

    def on_adjust(self, delta: int, multiplier: float = 1.0) -> None:
        pass

    def on_activate(self) -> Command | None:
        if self.callback is not None:
            return self.callback()
        return self.action

    def on_reset(self) -> None:
        pass

    def get_help_hint(self) -> str:
        return "[Enter] Select  [Esc] Back"
