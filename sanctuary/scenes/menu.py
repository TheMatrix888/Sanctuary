"""
Interactive hierarchical menu navigation system for Sanctuary.
Built on top of FormState and FormItem widgets.
"""
from sanctuary.core.state import Pop, Push, Quit
from sanctuary.scenes.arena import Arena, ArenaSimulation
from sanctuary.scenes.box import BouncingBoxState
from sanctuary.scenes.hammer import BouncingHammerState
from sanctuary.scenes.snowfall.config import CALM_DRIFT_CONFIG
from sanctuary.scenes.snowfall.state import SnowfallState
from sanctuary.scenes.text_wave import RainbowTextState
from sanctuary.ui.form import FormState
from sanctuary.ui.widgets import Button


def create_main_menu() -> FormState:
    """Builds the canonical hierarchical menu structure for Sanctuary."""

    def effects_menu() -> FormState:
        return FormState(
            title="Effects menu",
            items=[
                Button("Rainbow Text Wave", Push(RainbowTextState())),
                Button("Snowfall (5 Presets)", Push(SnowfallState(CALM_DRIFT_CONFIG))),
                Button("Bouncing Hammer", Push(BouncingHammerState())),
                Button("Bouncing Box", Push(BouncingBoxState())),
                Button("Back", Pop()),
            ],
            on_cancel=Pop(),
        )

    def arena_menu():
        return FormState(
            title="Arena menu",
            items=[
                Button("Arena", Push(Arena())),
                Button("Arena simulation [WIP]", Push(ArenaSimulation())),
            ],
            on_cancel=Pop(),
        )

    return FormState(
        title="Sanctuary Main Menu",
        items=[
            Button("Effects", Push(effects_menu())),
            Button("Arena", Push(arena_menu())),
            Button("Quit", Quit()),
        ],
        on_cancel=Quit(),
    )
