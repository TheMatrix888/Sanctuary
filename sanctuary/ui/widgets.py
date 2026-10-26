"""
Declarative, polymorphic TUI Form widgets and controls.
Provides interactive items for numeric parameter adjustments, discrete choices, and actions.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Color, DEFAULT_BG
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command


class FormItem(ABC):
    """Abstract interface for interactive form and inspector rows."""
    label: str
    is_selectable: bool = True

    @property
    def is_capturing_input(self) -> bool:
        """Indicates whether this widget intercepts form navigation (modal focus)."""
        return False

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

    @classmethod
    def integer(
        cls,
        label: str,
        value: int,
        min_value: int,
        max_value: int,
        delta: int = 1,
        suffix: str = "",
        default_value: int | None = None,
    ) -> "Knob":
        """Convenience factory for integer parameter controllers."""
        return cls(
            label=label,
            value=float(value),
            min_value=float(min_value),
            max_value=float(max_value),
            delta=float(delta),
            precision=0,
            default_value=float(default_value) if default_value is not None else None,
            suffix=suffix,
        )


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
    def value(self) -> str:
        if 0 <= self.index < len(self.values):
            return self.values[self.index]
        return ""

    def render_value(self) -> str:
        return f"[{self.value}]"

    def on_adjust(self, delta: int, multiplier: float = 1.0) -> None:
        if self.values:
            self.index = (self.index + delta) % len(self.values)

    def on_activate(self) -> Command | None:
        self.on_adjust(1)
        return None

    def on_reset(self) -> None:
        if self.default_index is not None:
            self.index = self.default_index

    def get_help_hint(self) -> str:
        return "[Enter/←/→] Cycle option  [R] Reset  [Esc] Back"


@dataclass(slots=True)
class Toggle(FormItem):
    """Boolean toggle switch with On/Off or custom true/false representations."""
    label: str
    is_enabled: bool = True
    default_enabled: bool | None = None
    on_label: str = "On"
    off_label: str = "Off"

    def __post_init__(self) -> None:
        if self.default_enabled is None:
            self.default_enabled = self.is_enabled

    @property
    def value(self) -> bool:
        return self.is_enabled

    def render_value(self) -> str:
        text = self.on_label if self.is_enabled else self.off_label
        return f"[{text}]"

    def on_adjust(self, delta: int, multiplier: float = 1.0) -> None:
        if delta != 0:
            self.is_enabled = not self.is_enabled

    def on_activate(self) -> Command | None:
        self.is_enabled = not self.is_enabled
        return None

    def on_reset(self) -> None:
        if self.default_enabled is not None:
            self.is_enabled = self.default_enabled

    def get_help_hint(self) -> str:
        return "[Enter/←/→] Toggle  [R] Reset  [Esc] Back"


@dataclass(slots=True)
class Button(FormItem):
    """Action button triggering a State Stack Command or callable action on Enter."""
    label: str
    action: Command | Callable[[], Command | None] | None = None

    def render_value(self) -> str:
        return ""

    def on_adjust(self, delta: int, multiplier: float = 1.0) -> None:
        pass

    def on_activate(self) -> Command | None:
        if callable(self.action):
            return self.action()
        return self.action

    def on_reset(self) -> None:
        pass

    def get_help_hint(self) -> str:
        return "[Enter] Select  [Esc] Back"


@dataclass(slots=True)
class Header(FormItem):
    """Non-selectable decorative section header or divider."""
    label: str
    color: Color = Color(140, 180, 240)
    is_selectable: bool = False

    def render_value(self) -> str:
        return ""

    def on_adjust(self, delta: int, multiplier: float = 1.0) -> None:
        pass

    def on_activate(self) -> Command | None:
        return None

    def on_reset(self) -> None:
        pass

    def get_help_hint(self) -> str:
        return ""


@dataclass(slots=True)
class Spacer(FormItem):
    """Non-selectable vertical spacing row."""
    label: str = ""
    is_selectable: bool = False

    def render_value(self) -> str:
        return ""

    def on_adjust(self, delta: int, multiplier: float = 1.0) -> None:
        pass

    def on_activate(self) -> Command | None:
        return None

    def on_reset(self) -> None:
        pass

    def get_help_hint(self) -> str:
        return ""



@dataclass(slots=True)
class Dropdown(FormItem):
    """
    Interactive dropdown selector with modal focus capture for list navigation.
    When collapsed, displays active option with expand indicator.
    When expanded, captures keyboard focus to navigate options list.
    """
    label: str
    options: list[str]
    selected_index: int = 0
    is_open: bool = False
    on_select: Callable[[str], Command | None] | None = None
    max_visible_options: int = 6

    def __post_init__(self) -> None:
        if self.options:
            self.selected_index = max(0, min(self.selected_index, len(self.options) - 1))
        else:
            self.selected_index = 0

    @property
    def is_capturing_input(self) -> bool:
        return self.is_open

    @property
    def value(self) -> str:
        if self.options and 0 <= self.selected_index < len(self.options):
            return self.options[self.selected_index]
        return ""

    def render_value(self) -> str:
        arrow = "▲" if self.is_open else "▼"
        current_text = self.value if self.value else "<Empty>"
        return f"[{current_text} {arrow}]"

    def on_adjust(self, delta: int, multiplier: float = 1.0) -> None:
        if not self.is_open and self.options:
            self.selected_index = (self.selected_index + delta) % len(self.options)

    def on_activate(self) -> Command | None:
        if not self.options:
            return None
        self.is_open = not self.is_open
        return None

    def on_reset(self) -> None:
        self.selected_index = 0
        self.is_open = False

    def get_help_hint(self) -> str:
        if self.is_open:
            return "[↑/↓] Select  [Enter] Confirm  [Esc] Close"
        return "[Enter] Open list  [←/→] Quick cycle  [R] Reset  [Esc] Back"

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        if not self.is_open or not self.options:
            self.is_open = False
            return None

        if input_handler.is_repeated(Key.UP) or input_handler.is_repeated(Key.W):
            self.selected_index = (self.selected_index - 1) % len(self.options)
            return None

        if input_handler.is_repeated(Key.DOWN) or input_handler.is_repeated(Key.S):
            self.selected_index = (self.selected_index + 1) % len(self.options)
            return None

        if input_handler.just_pressed(Key.ENTER):
            self.is_open = False
            if self.on_select is not None:
                return self.on_select(self.value)
            return None

        if input_handler.just_pressed(Key.ESC):
            self.is_open = False
            return None

        return None

    def draw_open_list(self, screen: Screen, x: int, start_y: int, max_y: int) -> int:
        current_y = start_y
        if not self.options:
            screen.draw_text(
                x=x,
                y=current_y,
                text="  <No saved options found>",
                fg_color=Color(120, 120, 140),
            )
            return current_y + 1

        total = len(self.options)
        window_size = min(self.max_visible_options, max_y - start_y)
        if window_size <= 0:
            return current_y

        half_window = window_size // 2
        start_idx = max(0, min(self.selected_index - half_window, total - window_size))
        end_idx = min(total, start_idx + window_size)

        for idx in range(start_idx, end_idx):
            if current_y > max_y:
                break
            option_text = self.options[idx]
            is_selected = (idx == self.selected_index)
            prefix = "► " if is_selected else "  "
            full_text = f"{prefix}{option_text}"
            fg = Color(255, 230, 120) if is_selected else Color(180, 190, 210)
            bg = Color(35, 45, 65) if is_selected else DEFAULT_BG

            screen.draw_text(
                x=x,
                y=current_y,
                text=full_text,
                fg_color=fg,
                bg_color=bg,
            )
            current_y += 1

        if total > window_size:
            screen.draw_text(
                x=x,
                y=current_y,
                text=f"  ({self.selected_index + 1}/{total}) [↑/↓ Scroll, Enter Select, Esc Close]",
                fg_color=Color(130, 140, 160),
            )
            current_y += 1

        return current_y
