"""
Arena Running State — Live tournament inspector and runtime execution controls.
Coordinates real-time gladiator battles, generational statistics, and background multiprocessing worker.
"""
from __future__ import annotations

import queue
from multiprocessing import Event, Process, Queue
from multiprocessing.synchronize import Event as EventType
from pathlib import Path
from typing import TYPE_CHECKING

from sanctuary.core.formatting import format_compact
from sanctuary.core.geometry import Size
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import CommandResult, Pop, TerminateProcess
from sanctuary.ui.form import FormState
from sanctuary.ui.widgets import Button, ChoiceKnob, Header, Knob, Spacer

from .config import (
    ARENA_ORIGIN,
    ARENA_SIMULATION_PROCESS_NAME,
)
from .models import (
    GpsTracker,
    Mode,
    PlaybackSettings,
    Snapshot,
    WorldConfig,
)
from .persistence import list_simulation_saves, save_simulation
from .worker import run_simulation_worker

if TYPE_CHECKING:
    from .setup import ArenaSetupState


class ArenaRunningState(FormState):
    """
    Active tournament inspector and playback control state.
    Renders live gladiator battles, generational statistics, and interactive pacing controls.
    """
    setup_state: ArenaSetupState
    world_config: WorldConfig
    saves_dir: Path
    is_running: bool
    snapshot_queue: Queue
    playback_queue: Queue
    stop_event: EventType
    last_snapshot: Snapshot | None
    gps_tracker: GpsTracker
    fps_knob: Knob
    mode_knob: ChoiceKnob
    stop_button: Button
    save_button: Button
    back_button: Button
    _last_fps: float
    _last_mode: str
    status_message: str
    status_message_timer: float

    def __init__(
        self,
        setup_state: ArenaSetupState,
        world_config: WorldConfig,
        saves_dir: Path,
    ) -> None:
        self.setup_state = setup_state
        self.world_config = world_config
        self.saves_dir = saves_dir
        self.is_running = False

        self.snapshot_queue = Queue(maxsize=2)
        self.playback_queue = Queue(maxsize=10)
        self.stop_event = Event()
        self.last_snapshot = None
        self.gps_tracker = GpsTracker()
        self.gps_tracker.reset(world_config.initial_generation)

        self._last_fps = 0.0
        self._last_mode = ""
        self.status_message = ""
        self.status_message_timer = 0.0

        self.stop_button = Button("Stop simulation", action=self._on_stop)
        self.fps_knob = Knob.integer("Snapshots per second", value=1, min_value=1, max_value=60, suffix="fps")
        self.mode_knob = ChoiceKnob("Mode", [mode.value for mode in Mode])
        self.save_button = Button("Save current genome", action=self._on_save)
        self.back_button = Button("Back", action=Pop())

        super().__init__(
            title="Arena Tournament",
            items=[
                self.stop_button,
                Spacer(),
                Header("--- Active Simulation Controls ---", color=Color(80, 255, 120)),
                Spacer(),
                self.fps_knob,
                self.mode_knob,
                self.save_button,
                self.back_button,
            ],
            on_cancel=Pop(),
        )

    def create_worker_process(self) -> Process:
        """Instantiates the headless background simulation process with configured IPC channels."""
        playback_settings = self.gather_playback_settings()
        self._last_fps = playback_settings.snapshots_per_second
        self._last_mode = playback_settings.mode.value
        return Process(
            target=run_simulation_worker,
            args=(
                self.world_config,
                playback_settings,
                self.playback_queue,
                self.snapshot_queue,
                self.stop_event,
            ),
            name=ARENA_SIMULATION_PROCESS_NAME,
            daemon=True,
        )

    def gather_playback_settings(self) -> PlaybackSettings:
        """Extracts dynamic playback pacing parameters from interactive controls."""
        return PlaybackSettings(
            snapshots_per_second=self.fps_knob.value,
            mode=Mode(self.mode_knob.value),
        )

    def _on_stop(self) -> CommandResult:
        """Stops background evolution worker, captures trailing snapshot, and returns to setup state."""
        self.stop_event.set()
        while not self.snapshot_queue.empty():
            try:
                self.last_snapshot = self.snapshot_queue.get_nowait()
            except queue.Empty:
                break
        self.gps_tracker.reset()
        self.is_running = False

        self.setup_state.last_snapshot = self.last_snapshot
        self.setup_state.start_button.label = "Start simulation"
        if self.last_snapshot is not None:
            self.setup_state.save_button.label = (
                f"Save latest snapshot genome (Gen {format_compact(self.last_snapshot.generation)})"
            )
        else:
            self.setup_state.save_button.label = "Save latest snapshot genome [None]"

        return TerminateProcess(ARENA_SIMULATION_PROCESS_NAME), Pop()

    def _on_save(self) -> None:
        """Serializes current active teams into a timestamped genome bundle."""
        if self.last_snapshot is None or not self.last_snapshot.teams:
            self.status_message = "Cannot save: No simulation snapshot available yet!"
            self.status_message_timer = 3.0
            return

        try:
            saved_path = save_simulation(
                teams=self.last_snapshot.teams,
                generation=self.last_snapshot.generation,
                world_config=self.world_config,
                directory=self.saves_dir,
            )
            self.setup_state.load_dropdown.options = list_simulation_saves(self.saves_dir)
            self.status_message = f"Saved: {saved_path.name}"
            self.status_message_timer = 4.0
        except Exception as error:
            self.status_message = f"Save failed: {error}"
            self.status_message_timer = 4.0

    def update(self, dt: float, screen_size: Size) -> None:
        super().update(dt, screen_size)
        if self.status_message_timer > 0.0:
            self.status_message_timer -= dt
            if self.status_message_timer <= 0.0:
                self.status_message = ""

        if not self.snapshot_queue.empty():
            self.last_snapshot = self.snapshot_queue.get()
            self.gps_tracker.update(self.last_snapshot.generation)
            self.setup_state.last_snapshot = self.last_snapshot

        if self.is_running:
            current_fps = self.fps_knob.value
            current_mode = self.mode_knob.value
            if current_fps != self._last_fps or current_mode != self._last_mode:
                self._last_fps = current_fps
                self._last_mode = current_mode
                playback_settings = self.gather_playback_settings()
                try:
                    self.playback_queue.put_nowait(playback_settings)
                except queue.Full:
                    pass

    def draw(self, screen: Screen) -> None:
        super().draw(screen)

        mode = self.mode_knob.value
        status_y = screen.size.rows - 2
        status_badge = f"[{mode.upper()}]"
        status_fg = Color(80, 255, 120) if mode != Mode.PAUSE else Color(255, 200, 80)

        screen.draw_text(
            x=2,
            y=status_y,
            text=f" Simulation State: {status_badge}",
            fg_color=status_fg,
        )
        if self.status_message:
            screen.draw_text(
                x=35,
                y=status_y,
                text=f"[!] {self.status_message}",
                fg_color=Color(255, 230, 100),
            )

        x_start, y_start = ARENA_ORIGIN.x, ARENA_ORIGIN.y
        if self.last_snapshot:
            snapshot = self.last_snapshot
            snapshot.tilemap.draw(screen, x_start, y_start)
            for team in snapshot.teams:
                for gladiator in team:
                    gladiator.draw(screen, x_start, y_start)

            if self.gps_tracker.rate > 0 and mode == Mode.SIMULATION:
                gps_suffix = f" ({int(self.gps_tracker.rate)} gen/s)"
            else:
                gps_suffix = ""

            y_info = y_start + snapshot.tilemap.height + 1
            screen.draw_text(
                x_start,
                y_info,
                f"generation {format_compact(snapshot.generation)}{gps_suffix} | turn {snapshot.turn}",
                fg_color=status_fg,
            )
            screen.draw_text(
                x_start,
                y_info + 1,
                f"best generation {format_compact(snapshot.record.generation)} [{snapshot.record.survivors} alive, {snapshot.record.turns} turns]",
                fg_color=status_fg,
            )
