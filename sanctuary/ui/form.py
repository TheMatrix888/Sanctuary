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
        self.ensure_selectable_index()

    def ensure_selectable_index(self) -> None:
        """Guarantees cursor index points to an interactive, selectable item."""
        if not self.items:
            self.index = 0
            return
        self.index = min(max(0, self.index), len(self.items) - 1)
        if self.items[self.index].is_selectable:
            return
        for offset in range(len(self.items)):
            fwd = (self.index + offset) % len(self.items)
            if self.items[fwd].is_selectable:
                self.index = fwd
                return

    def _navigate(self, step: int) -> None:
        """Cycles cursor index skipping non-selectable section headers and spacers."""
        selectable_indices = [idx for idx, item in enumerate(self.items) if item.is_selectable]
        if not selectable_indices:
            return
        new_index = (self.index + step) % len(self.items)
        while not self.items[new_index].is_selectable:
            new_index = (new_index + step) % len(self.items)
        self.index = new_index

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        if not self.items:
            if input_handler.just_pressed(Key.ESC):
                return self.on_cancel
            return None

        self.ensure_selectable_index()

        current_item = self.items[self.index]
        if current_item.is_capturing_input:
            command = current_item.handle_input(input_handler)
            if command is not None:
                return command
            return None

        # Vertical navigation
        if input_handler.is_repeated(Key.UP) or input_handler.is_repeated(Key.W):
            self._navigate(-1)
        if input_handler.is_repeated(Key.DOWN) or input_handler.is_repeated(Key.S):
            self._navigate(1)

        current_item = self.items[self.index]
        is_accelerated = input_handler.is_pressed(Key.CTRL)
        multiplier = 10.0 if is_accelerated else 1.0

        # Horizontal adjustment
        if input_handler.is_repeated(Key.LEFT) or input_handler.is_repeated(Key.A):
            current_item.on_adjust(-1, multiplier)
        if input_handler.is_repeated(Key.RIGHT) or input_handler.is_repeated(Key.D):
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
        selectable_num = 1
        y = start_y
        for i, item in enumerate(self.items):
            if y >= rows - 1:
                break

            if not item.is_selectable:
                if item.label:
                    color = getattr(item, "color", Color(140, 180, 240))
                    screen.draw_text(
                        x=2,
                        y=y,
                        text=f"    {item.label}",
                        fg_color=color,
                    )
                y += 1
                continue

            hover = (i == self.index)
            prefix = "--> " if hover else "    "
            value_str = item.render_value()
            if value_str:
                label_text = f"{prefix}{selectable_num}. {item.label} {value_str}"
            else:
                label_text = f"{prefix}{selectable_num}. {item.label}"
            selectable_num += 1

            fg = Color(120, 240, 255) if hover else Color(140, 150, 170)
            bg = Color(24, 32, 48) if hover else DEFAULT_BG

            screen.draw_text(
                x=2,
                y=y,
                text=label_text,
                fg_color=fg,
                bg_color=bg,
            )
            y += 1

            # Render expanded sub-options if item is capturing input
            if item.is_capturing_input:
                y = item.draw_expanded(screen, x=6, start_y=y, max_y=rows - 2)

        # Dynamic contextual bottom help bar
        if self.items and 0 <= self.index < len(self.items) and self.items[self.index].is_selectable:
            hover_item = self.items[self.index]
            if hover_item.is_capturing_input:
                help_text = f" {hover_item.get_help_hint()} "
            else:
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
