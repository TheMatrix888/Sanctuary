"""
Arena Simulation Form State — Parameter inspector and genetic tournament configuration.
Coordinates evolutionary bytecode gladiators in an isolated multiprocessing worker.
"""
import queue
import time
from multiprocessing import Event, Process, Queue
from multiprocessing.synchronize import Event as EventType

from sanctuary.core.clock import Timer
from sanctuary.core.geometry import Rect, Size
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Pop
from sanctuary.ui.form import FormState
from sanctuary.ui.widgets import Button, ChoiceKnob, Header, Knob, Spacer, Toggle

from .config import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    EXCLUSION_HEIGHT,
    EXCLUSION_WIDTH,
    BEST_PER_GENERATION,
    GPS_METRICS_INTERVAL,
    MAX_GENERATION_TURNS,
    MUTATION_GENES_COUNT,
    MUTATION_RATE_PERCENT,
)
from .generators import ARENA_PRESETS
from .tile_map import TileMap
from .worker import (
    GenerationRecord,
    Mode,
    PlaybackSettings,
    Snapshot,
    WorldConfig,
    run_simulation_worker,
)


class ArenaSimulation(FormState):
    """
    Inspector and tournament configurator state for the evolutionary arena simulation.
    Allows configuring gladiator entity counts, snapshot rates, maps, and runtime execution.
    """
    is_running: bool
    sim_button: Button
    setup_header: Header
    live_header: Header
    tournament_header: Header
    max_turns_knob: Knob
    champions_knob: Knob
    mutation_rate_knob: Knob
    mutation_genes_knob: Knob
    exclusion_width_knob: Knob
    exclusion_height_knob: Knob
    exclusion_blink_toggle: Toggle
    blink_timer: Timer
    _exclusion_visible: bool
    entities_knob: Knob
    fps_knob: Knob
    mode_knob: ChoiceKnob
    map_knob: ChoiceKnob
    load_button: Button
    save_button: Button
    back_button: Button
    process: Process | None
    snapshot_queue: Queue
    playback_queue: Queue
    stop_event: EventType
    last_snapshot: Snapshot | None
    current_map: str
    map_preview: TileMap
    _last_fps: float
    _last_mode: str
    gps: float
    _last_gps_time: float
    _last_gps_generation: int

    def __init__(self) -> None:
        self.is_running = False
        self.snapshot_queue = Queue(maxsize=2)
        self.playback_queue = Queue(maxsize=10)
        self.stop_event = Event()
        self.process = None
        self.last_snapshot = None
        self._last_fps = 0.0
        self._last_mode = ""
        self.gps = 0.0
        self._last_gps_time = time.perf_counter()
        self._last_gps_generation = 1
        self.blink_timer = Timer(0.5)
        self._exclusion_visible = True

        self._build_widgets()

        super().__init__(
            title="Arena Simulation",
            items=[],
            on_cancel=Pop(),
        )

        self._update_active_items()
        self.update_map_preview()

    def _build_widgets(self) -> None:
        """Instantiates compact form widgets, knobs, and decorative section headers."""
        self.sim_button = Button("Start simulation", action=self._toggle_simulation)
        self.setup_header = Header("--- Simulation Setup ---", color=Color(245, 110, 115))
        self.live_header = Header("--- Active Simulation Controls ---", color=Color(80, 255, 120))

        self.entities_knob = Knob.integer("Entities per team", value=10, min_value=1, max_value=100, suffix="entities")
        self.fps_knob = Knob.integer("Snapshots per second", value=1, min_value=1, max_value=60, suffix="fps")
        self.mode_knob = ChoiceKnob("Mode", [mode.value for mode in Mode])
        self.map_knob = ChoiceKnob("Map", list(ARENA_PRESETS.keys()))
        self.exclusion_width_knob = Knob.integer(
            "Exclusion width",
            value=EXCLUSION_WIDTH,
            min_value=0,
            max_value=ARENA_WIDTH - 2,
            suffix="cells",
        )
        self.exclusion_height_knob = Knob.integer(
            "Exclusion height",
            value=EXCLUSION_HEIGHT,
            min_value=0,
            max_value=ARENA_HEIGHT - 2,
            suffix="cells",
        )
        self.exclusion_blink_toggle = Toggle("Blink exclusion zone", is_enabled=True)

        self.tournament_header = Header("--- Tournament & Evolution ---", color=Color(255, 180, 80))
        self.max_turns_knob = Knob.integer(
            "Max turns per epoch",
            value=MAX_GENERATION_TURNS,
            min_value=100,
            max_value=2000,
            delta=10,
            suffix="turns",
        )
        self.champions_knob = Knob.integer(
            "Champions to clone",
            value=BEST_PER_GENERATION,
            min_value=1,
            max_value=int(self.entities_knob.value),
            suffix="champions",
        )
        self.mutation_rate_knob = Knob.integer(
            "Mutation rate",
            value=MUTATION_RATE_PERCENT,
            min_value=0,
            max_value=100,
            suffix="%",
        )
        self.mutation_genes_knob = Knob.integer(
            "Mutated genes",
            value=MUTATION_GENES_COUNT,
            min_value=1,
            max_value=16,
            suffix="genes",
        )

        self.load_button = Button("Load genome [WIP]")
        self.save_button = Button("Save genome [WIP]")
        self.back_button = Button("Back", action=Pop())

    def update_map_preview(self) -> None:
        self.current_map = self.map_knob.value
        self.map_preview = ARENA_PRESETS[self.current_map](ARENA_WIDTH, ARENA_HEIGHT)

    def _update_active_items(self) -> None:
        if self.is_running:
            self.items = [
                self.sim_button,
                Spacer(),
                self.live_header,
                Spacer(),
                self.fps_knob,
                self.mode_knob,
                self.save_button,
                self.back_button,
            ]
        else:
            self.items = [
                self.sim_button,
                Spacer(),
                self.setup_header,
                self.entities_knob,
                self.map_knob,
                self.exclusion_width_knob,
                self.exclusion_height_knob,
                self.exclusion_blink_toggle,
                Spacer(),
                self.tournament_header,
                self.max_turns_knob,
                self.champions_knob,
                self.mutation_rate_knob,
                self.mutation_genes_knob,
                Spacer(),
                self.load_button,
                self.back_button,
            ]
        self.ensure_selectable_index()

    def gather_world_config(self) -> WorldConfig:
        """Extracts immutable configuration parameters for tournament genesis."""
        return WorldConfig(
            entities_per_team=int(self.entities_knob.value),
            map=self.map_knob.value,
            max_turns=int(self.max_turns_knob.value),
            best_per_generation=int(self.champions_knob.value),
            mutation_rate_percent=int(self.mutation_rate_knob.value),
            mutation_genes_count=int(self.mutation_genes_knob.value),
            exclusion_width=int(self.exclusion_width_knob.value),
            exclusion_height=int(self.exclusion_height_knob.value),
        )

    def gather_playback_settings(self) -> PlaybackSettings:
        """Extracts dynamic playback pacing parameters from interactive controls."""
        return PlaybackSettings(
            snapshots_per_second=self.fps_knob.value,
            mode=Mode(self.mode_knob.value),
        )

    def _toggle_simulation(self) -> Command | None:
        """Toggles simulation execution state and synchronizes button label."""
        if not self.is_running:
            self.stop_event.clear()
            self.gps = 0.0
            self._last_gps_time = time.perf_counter()
            self._last_gps_generation = 1
            world_config = self.gather_world_config()
            playback_settings = self.gather_playback_settings()
            self._last_fps = playback_settings.snapshots_per_second
            self._last_mode = playback_settings.mode.value

            self.process = Process(
                target=run_simulation_worker,
                args=(
                    world_config,
                    playback_settings,
                    self.playback_queue,
                    self.snapshot_queue,
                    self.stop_event,
                ),
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
            self.gps = 0.0

        self.is_running = not self.is_running
        self.sim_button.label = "Stop simulation" if self.is_running else "Start simulation"
        self._update_active_items()
        return None

    def update(self, dt: float, screen_size: Size) -> None:
        super().update(dt, screen_size)
        self.champions_knob.max_value = float(self.entities_knob.value)
        self.champions_knob.value = min(self.champions_knob.value, self.champions_knob.max_value)

        if self.blink_timer.tick(dt):
            self._exclusion_visible = not self._exclusion_visible
        if not self.snapshot_queue.empty():
            self.last_snapshot = self.snapshot_queue.get()
            now = time.perf_counter()
            elapsed = now - self._last_gps_time
            if elapsed >= GPS_METRICS_INTERVAL:
                delta_gen = self.last_snapshot.generation - self._last_gps_generation
                self.gps = max(0.0, delta_gen / elapsed)
                self._last_gps_time = now
                self._last_gps_generation = self.last_snapshot.generation

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

        if self.current_map != self.map_knob.value:
            self.update_map_preview()

    def draw(self, screen: Screen) -> None:
        super().draw(screen)

        mode = self.mode_knob.value

        status_y = screen.size.rows - 2
        if self.is_running:
            status_badge = f"[{mode.upper()}]"
            status_fg = Color(80, 255, 120) if mode != Mode.PAUSE else Color(255, 200, 80)
        else:
            status_badge = "[STOPPED]"
            status_fg = Color(245, 110, 115)

        status_text = f" Simulation State: {status_badge}"
        screen.draw_text(
            x=2,
            y=status_y,
            text=status_text,
            fg_color=status_fg,
        )

        x_start, y_start = 55, 3
        if self.last_snapshot and self.is_running:
            snapshot = self.last_snapshot
            snapshot.tilemap.draw(screen, x_start, y_start)
            for team in snapshot.teams:
                for gladiator in team:
                    gladiator.draw(screen, x_start, y_start)

            if self.gps > 0 and mode == Mode.SIMULATION:
                gps_suffix = f" ({self.gps:.0f} gen/s)"
            else:
                gps_suffix = ""

            y_info = y_start + snapshot.tilemap.height + 1
            screen.draw_text(
                x_start,
                y_info,
                f"generation {snapshot.generation}{gps_suffix} | turn {snapshot.turn}",
                fg_color=status_fg,
            )
            screen.draw_text(
                x_start,
                y_info + 1,
                f"best generation {snapshot.record.generation} [{snapshot.record.survivors} alive, {snapshot.record.turns} turns]",
                fg_color=status_fg,
            )
        else:
            self.map_preview.draw(screen, x_start, y_start)
            if self.exclusion_blink_toggle.value and self._exclusion_visible:
                exclusion_width = int(self.exclusion_width_knob.value)
                exclusion_height = int(self.exclusion_height_knob.value)
                if exclusion_width > 0 and exclusion_height > 0:
                    exclusion_rect = Rect.from_center(
                        center_x=ARENA_WIDTH // 2,
                        center_y=ARENA_HEIGHT // 2,
                        width=exclusion_width,
                        height=exclusion_height,
                    )
                    for point in exclusion_rect:
                        if 0 <= point.x < ARENA_WIDTH and 0 <= point.y < ARENA_HEIGHT:
                            screen.draw_text(
                                x=x_start + point.x,
                                y=y_start + point.y,
                                text="x",
                                fg_color=Color(255, 60, 60),
                            )
