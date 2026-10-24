"""
Arena Simulation Form State — Parameter inspector and genetic tournament configuration.
Coordinates evolutionary bytecode gladiators in an isolated multiprocessing worker.
"""
from multiprocessing import Event, Process, Queue
from multiprocessing.synchronize import Event as EventType

from sanctuary.core.geometry import Size
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Pop
from sanctuary.ui.form import FormState
from sanctuary.ui.widgets import Button, ChoiceKnob, Knob

from .config import ARENA_HEIGHT, ARENA_WIDTH
from .generators import ARENA_PRESETS
from .tile_map import TileMap
from .worker import (
    SimulationSettings,
    Snapshot,
    run_simulation_worker,
)


class ArenaSimulation(FormState):
    """
    Inspector and tournament configurator state for the evolutionary arena simulation.
    Allows configuring gladiator entity counts, snapshot rates, maps, and runtime execution.
    """
    is_running: bool
    sim_button: Button
    entities_knob: Knob
    fps_knob: Knob
    mode_knob: ChoiceKnob
    map_knob: ChoiceKnob
    process: Process | None
    queue: Queue
    stop_event: EventType
    last_snapshot: Snapshot | None
    current_map: str
    map_preview: TileMap

    def __init__(self) -> None:
        self.is_running = False
        self.queue = Queue(maxsize=2)
        self.stop_event = Event()
        self.process = None
        self.last_snapshot = None

        self.sim_button = Button(
            label="Start simulation",
            action=self._toggle_simulation,
        )
        self.entities_knob = Knob(
            label="Entities per team",
            value=10.0,
            min_value=1.0,
            max_value=20.0,
            delta=1.0,
            precision=0,
            suffix="entities",
        )
        self.fps_knob = Knob(
            label="Snapshots per second",
            value=2.0,
            min_value=1.0,
            max_value=60.0,
            delta=1.0,
            precision=2,
            suffix="fps",
        )
        self.mode_knob = ChoiceKnob(
            label="Mode",
            values=[
                "Simulation",
                "Theatre (fps = turns per second)",
            ],
            index=0,
        )
        self.map_knob = ChoiceKnob(
            label="Map",
            values=[
                "Colosseum Arena",
                "Concentric Bastions",
                "Greek Amphitheater",
                "Tectonic Chasm",
                "Sierpinski Ruins",
                "Empty Proving Ground",
            ],
            index=0,
        )

        self.load_button = Button(
            label="Load genome [WIP]",
            action=None,
        )

        self.save_button = Button(
            label="Save genome [WIP]",
            action=None,
        )
        self.back_button = Button(
            label="Back",
            action=Pop(),
        )

        super().__init__(
            title="Arena Simulation",
            items=[],
            on_cancel=Pop(),
        )

        self._update_active_items()

        self.update_map_preview()

    def update_map_preview(self) -> None:
        self.current_map = self.map_knob.current_value
        self.map_preview = ARENA_PRESETS[self.current_map](ARENA_WIDTH, ARENA_HEIGHT)

    def _update_active_items(self) -> None:
        if self.is_running:
            self.items = [self.sim_button, self.fps_knob, self.mode_knob, self.save_button, self.back_button]
        else:
            self.items = [self.sim_button, self.entities_knob, self.map_knob, self.load_button, self.back_button]
        self.index = min(self.index, len(self.items) - 1)

    def gather_settings(self) -> SimulationSettings:
        """Extracts configuration settings from UI widget state."""
        return SimulationSettings(
            entities_per_team=int(self.entities_knob.value),
            snapshots_per_second=self.fps_knob.value,
            mode=self.mode_knob.current_value,
            map=self.map_knob.current_value,
        )

    def _toggle_simulation(self) -> Command | None:
        """Toggles simulation execution state and synchronizes button label."""
        if not self.is_running:
            self.stop_event.clear()
            settings = self.gather_settings()
            self.process = Process(
                target=run_simulation_worker,
                args=(self.queue, self.stop_event, settings),
            )
            self.process.start()
        else:
            self.stop_event.set()
            if self.process is not None:
                self.process.join(timeout=1.0)
                if self.process.is_alive():
                    self.process.terminate()
            self.process = None
            self.last_snapshot = None

        self.is_running = not self.is_running
        self.sim_button.label = "Stop simulation" if self.is_running else "Start simulation"
        self._update_active_items()
        return None

    def update(self, dt: float, screen_size: Size) -> None:
        super().update(dt, screen_size)
        if not self.queue.empty():
            self.last_snapshot = self.queue.get()

        if self.current_map != self.map_knob.current_value:
            self.update_map_preview()

    def draw(self, screen: Screen) -> None:
        super().draw(screen)

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

        x_start, y_start = 50, 3
        if self.last_snapshot and self.is_running:
            snapshot = self.last_snapshot
            snapshot.tilemap.draw(screen, x_start, y_start)
            for team in snapshot.teams:
                for gladiator in team:
                    gladiator.draw(screen, x_start, y_start)

            y_info = y_start + snapshot.tilemap.height + 1
            screen.draw_text(
                x_start,
                y_info,
                f"turn {snapshot.turn} | generation {snapshot.generation}",
                fg_color=status_fg,
            )
            screen.draw_text(
                x_start,
                y_info + 1,
                f"best generation {snapshot.longest_generation[0]} [{snapshot.longest_generation[1]} turns]",
                fg_color=status_fg,
            )
        else:
            self.map_preview.draw(screen, x_start, y_start)
