"""
Interactive hierarchical menu navigation system for Sanctuary.
"""
from dataclasses import dataclass

from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Color, DEFAULT_BG
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Quit, Push, Pop, State
from sanctuary.scenes.box import BouncingBoxState
from sanctuary.scenes.hammer import BouncingHammerState
from sanctuary.scenes.snowfall.config import CALM_DRIFT_CONFIG
from sanctuary.scenes.snowfall.state import SnowfallState
from sanctuary.scenes.text_wave import RainbowTextState


@dataclass(slots=True, frozen=True)
class MenuItem:
    """Represents a selectable menu entry and its transition command."""
    label: str
    action: Command | None = None


class Menu(State):
    """
    Keyboard-driven selection menu state.
    Supports circular arrow navigation (Up/Down, W/S), Enter execution, and Esc cancellation.
    """

    def __init__(self, title: str, items: list[MenuItem], on_cancel: Command | None = None):
        self.title = title
        self.items = items
        self.index = 0
        self.on_cancel = on_cancel

    def on_enter(self) -> None:
        """Resets selection index upon entering the menu."""
        self.index = 0

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        if input_handler.just_pressed(Key.UP) or input_handler.just_pressed(Key.W):
            self.index = (self.index - 1) % len(self.items)
        if input_handler.just_pressed(Key.DOWN) or input_handler.just_pressed(Key.S):
            self.index = (self.index + 1) % len(self.items)

        if input_handler.just_pressed(Key.ENTER):
            return self.items[self.index].action

        if input_handler.just_pressed(Key.ESC) and self.on_cancel is not None:
            return self.on_cancel

        return None

    def draw(self, screen: Screen) -> None:
        cols = screen.size.columns
        rows = screen.size.rows

        # Render menu header
        header_text = f"=== {self.title} ==="
        screen.draw_text(
            x=2,
            y=1,
            text=header_text,
            fg_color=Color(180, 210, 240)
        )

        start_y = 3
        for i, item in enumerate(self.items):
            y = start_y + i
            if y >= rows - 2:
                break
            hover = (i == self.index)
            prefix = "--> " if hover else "    "
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

        # Bottom help bar
        help_text = " [W/S, ↑/↓ Navigate] [Enter Select] [Esc Back] "
        screen.draw_text(
            x=0,
            y=rows - 1,
            text=help_text.ljust(cols)[:cols],
            fg_color=Color(160, 170, 190),
            bg_color=Color(20, 24, 32),
        )


def create_main_menu() -> Menu:
    """Builds the canonical hierarchical menu structure for Sanctuary."""

    def demo_menu() -> Menu:
        return Menu(
            title="Demonstration Suite",
            items=[
                MenuItem("Rainbow Text Wave", Push(RainbowTextState())),
                MenuItem("Snowfall (5 Presets)", Push(SnowfallState(CALM_DRIFT_CONFIG))),
                MenuItem("Bouncing Hammer", Push(BouncingHammerState())),
                MenuItem("Bouncing Box", Push(BouncingBoxState())),
                MenuItem("Tactical Battle [WIP]"),
                MenuItem("Back", Pop()),
            ],
            on_cancel=Pop(),
        )

    return Menu(
        title="Sanctuary Main Menu",
        items=[
            MenuItem("Demos", Push(demo_menu())),
            MenuItem("Quit", Quit()),
        ],
        on_cancel=Quit(),
    )
