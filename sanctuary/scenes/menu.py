"""
Interactive hierarchical menu navigation system for Sanctuary.
Built on top of FormState and FormItem widgets.
"""
from sanctuary.core.state import Pop, Push, Quit
from sanctuary.scenes.arena import Arena, ArenaSimulation
from sanctuary.scenes.demos import (
    BouncingBoxState,
    BouncingHammerState,
    GridAuditState,
    OrbitalWindowState,
    OvercomingState,
    RainbowTextState,
)
from sanctuary.scenes.snowfall.config import CALM_DRIFT_CONFIG
from sanctuary.scenes.snowfall.state import SnowfallState
from sanctuary.ui.form import FormState
from sanctuary.ui.widgets import Button


def create_main_menu() -> FormState:
    """Builds the canonical hierarchical menu structure for Sanctuary."""

    def demos_menu() -> FormState:
        return FormState(
            title="Demos menu",
            items=[
                Button("Rainbow Text Wave", lambda: Push(RainbowTextState())),
                Button("Snowfall (5 Presets)", Push(SnowfallState(CALM_DRIFT_CONFIG))),
                Button("Bouncing Hammer", lambda: Push(BouncingHammerState())),
                Button("Bouncing Box", lambda: Push(BouncingBoxState())),
                Button("Grid Audit (# Fill)", lambda: Push(GridAuditState())),
                Button("Overcoming (Sine Flex)", lambda: Push(OvercomingState())),
                Button("Orbital Window", Push(OrbitalWindowState())),
                Button("Back", Pop()),
            ],
            on_cancel=Pop(),
        )

    return FormState(
        title="Sanctuary Main Menu",
        items=[
            Button("Arena", lambda: Push(Arena())),
            Button("Arena simulation", Push(ArenaSimulation())),
            Button("Demos", Push(demos_menu())),
            Button("Quit", Quit()),
        ],
        on_cancel=Quit(),
    )
