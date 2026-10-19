"""
Arena Simulation Form State — Parameter inspector and genetic tournament configuration.
"""
from dataclasses import dataclass

from sanctuary.core.clock import Timer
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Pop
from sanctuary.ui.form import FormState
from sanctuary.ui.widgets import Button, ChoiceKnob, Knob

import multiprocessing


@dataclass(slots=True, frozen=True)
class SimulationSettings:
    entities_per_team: int
    snapshots_per_second: float
    real_time_mode: bool
    map: str


class SimulationWorker:
    timer: Timer

    def __init__(self, settings: SimulationSettings) -> None:
        self.reset(settings)

    def reset(self, settings: SimulationSettings) -> None:
        self.timer = Timer(1 / settings.snapshots_per_second)

    def run(self):
        pass


class ArenaSimulation(FormState):
    """
    Inspector and tournament configurator state for the evolutionary arena simulation.
    Allows configuring gladiator entity counts, snapshot rates, maps, and runtime execution.
    """
    is_running: bool
    sim_button: Button

    def __init__(self) -> None:
        self.is_running = False

        self.sim_button = Button(
            label="Start simulation",
            callback=self._toggle_simulation,
        )

        items = [
            self.sim_button,

            Button(
                label="Load genome",
                action=None,
            ),
            Button(
                label="Save genome",
                action=None,
            ),
            Knob(
                label="Entities per team",
                value=10.0,
                min_value=1.0,
                max_value=20.0,
                delta=1.0,
                precision=0,
                suffix="entities",
            ),
            Knob(
                label="Snapshots per second",
                value=1.0,
                min_value=0.25,
                max_value=30.0,
                delta=0.25,
                precision=2,
                suffix="fps",
            ),
            ChoiceKnob(
                label="Map",
                values=[
                    "Empty Proving Ground",
                    "Colosseum Arena",
                    "Concentric Bastions",
                    "Greek Amphitheater",
                    "Tectonic Chasm",
                    "Sierpinski Ruins",
                ],
                index=0,
            ),
            Button(
                label="Back",
                action=Pop(),
            ),
        ]

        super().__init__(
            title="Arena Simulation",
            items=items,
            on_cancel=Pop(),
        )

    def _toggle_simulation(self) -> Command | None:
        """Toggles simulation execution state and synchronizes button label."""
        if not self.is_running:
            pass
        else:
            pass

        self.is_running = not self.is_running
        self.sim_button.label = "Stop simulation" if self.is_running else "Start simulation"

    def draw(self, screen: Screen) -> None:
        super().draw(screen)

        # Simulation telemetry status line right above bottom help bar
        status_y = screen.size.rows - 2
        if self.is_running:
            status_badge = "[RUNNING]"
            status_fg = Color(80, 255, 120)
        else:
            status_badge = "[STOPPED]"
            status_fg = Color(160, 160, 180)

        status_text = f" Simulation State: {status_badge}"
        screen.draw_text(
            x=2,
            y=status_y,
            text=status_text,
            fg_color=status_fg,
        )
