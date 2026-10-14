"""
Reusable FormState supporting vertical navigation, polymorphic widget adjustment,
and dynamic contextual status bar hints.
"""
from collections.abc import Sequence

from sanctuary.core.geometry import Size
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Color, DEFAULT_BG
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Pop, State, ToggleMetrics
from sanctuary.ui.widgets import FormItem


class FormState(State):
    """
    Standard state presenting a vertical list of FormItems.
    Dispatches navigation, adjustments (with Ctrl accelerator), resets, and actions.
    """
    title: str
    items: list[FormItem]
    index: int
    on_cancel: Command | None

    def __init__(
        self,
        title: str,
        items: Sequence[FormItem],
        on_cancel: Command | None = Pop(),
    ) -> None:
        self.title = title
        self.items = list(items)
        self.index = 0
        self.on_cancel = on_cancel

    def on_enter(self) -> None:
        if self.items:
            self.index = min(self.index, len(self.items) - 1)

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        if not self.items:
            if input_handler.just_pressed(Key.ESC):
                return self.on_cancel
            return None

        # Vertical navigation
        if input_handler.just_pressed(Key.UP) or input_handler.just_pressed(Key.W):
            self.index = (self.index - 1) % len(self.items)
        if input_handler.just_pressed(Key.DOWN) or input_handler.just_pressed(Key.S):
            self.index = (self.index + 1) % len(self.items)

        current_item = self.items[self.index]
        is_accelerated = input_handler.is_pressed(Key.CTRL)
        multiplier = 10.0 if is_accelerated else 1.0

        # Horizontal adjustment
        if input_handler.just_pressed(Key.LEFT) or input_handler.just_pressed(Key.A):
            current_item.on_adjust(-1, multiplier)
        if input_handler.just_pressed(Key.RIGHT) or input_handler.just_pressed(Key.D):
            current_item.on_adjust(1, multiplier)

        # Value reset to default
        if input_handler.just_pressed(Key.R):
            current_item.on_reset()

        # Primary activation
        if input_handler.just_pressed(Key.ENTER):
            command = current_item.on_activate()
            if command is not None:
                return command

        # Navigation and telemetry
        if input_handler.just_pressed(Key.ESC):
            return self.on_cancel
        if input_handler.just_pressed(Key.F3):
            return ToggleMetrics()

        return None

    def update(self, dt: float, screen_size: Size) -> None:
        pass

    def draw(self, screen: Screen) -> None:
        cols = screen.size.columns
        rows = screen.size.rows

        # Header
        header_text = f"=== {self.title} ==="
        screen.draw_text(
            x=2,
            y=1,
            text=header_text,
            fg_color=Color(180, 210, 240),
        )

        # Items listing
        start_y = 3
        for i, item in enumerate(self.items):
            y = start_y + i
            if y >= rows - 1:
                break
            hover = (i == self.index)
            prefix = "--> " if hover else "    "
            value_str = item.render_value()
            if value_str:
                label_text = f"{prefix}{i + 1}. {item.label} {value_str}"
            else:
                label_text = f"{prefix}{i + 1}. {item.label}"

            fg = Color(120, 240, 255) if hover else Color(140, 150, 170)
            bg = Color(24, 32, 48) if hover else DEFAULT_BG

            screen.draw_text(
                x=2,
                y=y,
                text=label_text,
                fg_color=fg,
                bg_color=bg,
            )

        # Dynamic contextual bottom help bar
        if self.items:
            hover_item = self.items[self.index]
            help_text = f" [W/S, ↑/↓ Navigate] {hover_item.get_help_hint()} "
        else:
            help_text = " [Esc Back] "

        screen.draw_text(
            x=0,
            y=rows - 1,
            text=help_text.ljust(cols)[:cols],
            fg_color=Color(160, 170, 190),
            bg_color=Color(20, 24, 32),
        )
