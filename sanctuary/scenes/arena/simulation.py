"""
Arena Simulation Form State — Parameter inspector and genetic tournament configuration.
Coordinates evolutionary bytecode gladiators in an isolated multiprocessing worker.
"""
import queue
from multiprocessing import Event, Process, Queue
from multiprocessing.synchronize import Event as EventType
from pathlib import Path

from sanctuary.core.formatting import format_compact
from sanctuary.core.geometry import Rect, Size
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Pop
from sanctuary.ui.form import FormState
from sanctuary.ui.widgets import Button, ChoiceKnob, Dropdown, Header, Knob, Spacer, Toggle

from .persistence import (
    SAVES_DIR,
    list_simulation_saves,
    load_simulation,
    save_simulation,
)

from .config import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    DEFAULT_ENTITIES_PER_TEAM,
    EXCLUSION_HEIGHT,
    EXCLUSION_WIDTH,
    BEST_PER_GENERATION,
    MAX_GENERATION_TURNS,
    MUTATION_RATE_PERCENT,
)
from .generators import ARENA_PRESETS
from .models import (
    BlinkIndicator,
    GpsTracker,
    Mode,
    PlaybackSettings,
    Snapshot,
    WorldConfig,
)
from .tile_map import TileMap
from .worker import run_simulation_worker


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
    exclusion_width_knob: Knob
    exclusion_height_knob: Knob
    exclusion_blink_toggle: Toggle
    exclusion_blinker: BlinkIndicator
    entities_knob: Knob
    fps_knob: Knob
    mode_knob: ChoiceKnob
    map_knob: ChoiceKnob
    load_dropdown: Dropdown
    save_button: Button
    back_button: Button
    loaded_genomes: dict[str, list[list[int]]] | None
    loaded_generation: int
    status_message: str
    status_message_timer: float
    process: Process | None
    snapshot_queue: Queue
    playback_queue: Queue
    stop_event: EventType
    last_snapshot: Snapshot | None
    current_map: str
    map_preview: TileMap
    _last_fps: float
    _last_mode: str
    gps_tracker: GpsTracker
    saves_dir: Path

    def __init__(self, saves_dir: Path = SAVES_DIR) -> None:
        self.saves_dir = saves_dir
        self.is_running = False
        self.snapshot_queue = Queue(maxsize=2)
        self.playback_queue = Queue(maxsize=10)
        self.stop_event = Event()
        self.process = None
        self.last_snapshot = None
        self._last_fps = 0.0
        self._last_mode = ""
        self.gps_tracker = GpsTracker()
        self.exclusion_blinker = BlinkIndicator(0.5)
        self.loaded_genomes = None
        self.loaded_generation = 1
        self.status_message = ""
        self.status_message_timer = 0.0

        self._build_widgets()

        super().__init__(
            title="Arena Simulation",
            items=[],
            on_cancel=Pop(),
        )

        self._update_active_items()
        self.update_map_preview()

    @property
    def gps(self) -> float:
        return self.gps_tracker.rate

    @property
    def _exclusion_visible(self) -> bool:
        return self.exclusion_blinker.is_visible

    def _build_widgets(self) -> None:
        """Instantiates compact form widgets, knobs, and decorative section headers."""
        self.sim_button = Button("Start simulation", action=self._toggle_simulation)
        self.setup_header = Header("--- Simulation Setup ---", color=Color(245, 110, 115))
        self.live_header = Header("--- Active Simulation Controls ---", color=Color(80, 255, 120))

        self.entities_knob = Knob.integer("Entities per team", value=DEFAULT_ENTITIES_PER_TEAM, min_value=1, max_value=100, suffix="entities")
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
        self.mutation_rate_knob = Knob(
            "Gene mutation rate",
            value=MUTATION_RATE_PERCENT,
            min_value=0.0,
            max_value=100.0,
            delta=0.5,
            precision=1,
            suffix="%",
        )

        self.load_dropdown = Dropdown(
            "Load genome",
            options=list_simulation_saves(self.saves_dir),
            on_select=self._on_genome_loaded,
        )
        self.save_button = Button("Save genome", action=self._on_save_genome)
        self.back_button = Button("Back", action=Pop())

    def _on_save_genome(self) -> None:
        """Serializes current active teams into a timestamped genome bundle."""
        if self.last_snapshot is None or not self.last_snapshot.teams:
            self.status_message = "Cannot save: No simulation snapshot available yet!"
            self.status_message_timer = 3.0
            return

        try:
            saved_path = save_simulation(
                teams=self.last_snapshot.teams,
                generation=self.last_snapshot.generation,
                world_config=self.gather_world_config(),
                directory=self.saves_dir,
            )
            self.load_dropdown.options = list_simulation_saves(self.saves_dir)
            self.status_message = f"Saved: {saved_path.name}"
            self.status_message_timer = 4.0
        except Exception as error:
            self.status_message = f"Save failed: {error}"
            self.status_message_timer = 4.0

    def _on_genome_loaded(self, filename: str) -> None:
        """Loads and activates a saved genome bundle for subsequent simulation epochs."""
        if not filename:
            return

        try:
            path = Path(filename)
            if not path.is_file():
                path = self.saves_dir / path
            save = load_simulation(path)
            self.loaded_genomes = {
                "red": save.red_genomes,
                "blue": save.blue_genomes,
            }
            self.loaded_generation = save.generation
            self.set_world_config(save.world_config)
            self.last_snapshot = None
            self._update_active_items()

            count = len(save.red_genomes)
            self.status_message = f"Loaded {path.name} [{count} champions, Gen {format_compact(save.generation)}]"
            self.status_message_timer = 4.0
        except Exception as error:
            self.status_message = f"Load failed: {error}"
            self.status_message_timer = 4.0


    def update_map_preview(self) -> None:
        self.current_map = self.map_knob.value
        self.map_preview = ARENA_PRESETS[self.current_map](ARENA_WIDTH, ARENA_HEIGHT)

    def _update_active_items(self) -> None:
        if self.is_running:
            self.save_button.label = "Save current genome"
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
            if self.last_snapshot is not None:
                self.save_button.label = f"Save latest snapshot genome (Gen {format_compact(self.last_snapshot.generation)})"
            else:
                self.save_button.label = "Save latest snapshot genome [None]"

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
                Spacer(),
                self.load_dropdown,
                self.save_button,
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
            mutation_rate_percent=float(self.mutation_rate_knob.value),
            exclusion_size=Size(int(self.exclusion_width_knob.value), int(self.exclusion_height_knob.value)),
            initial_generation=self.loaded_generation,
            initial_genomes=self.loaded_genomes,
        )

    def set_world_config(self, config: WorldConfig) -> None:
        """Applies world configuration parameters directly to interactive knobs and updates preview."""
        self.entities_knob.value = config.entities_per_team
        self.map_knob.value = config.map
        self.max_turns_knob.value = config.max_turns
        self.champions_knob.value = config.best_per_generation
        self.mutation_rate_knob.value = config.mutation_rate_percent
        self.exclusion_width_knob.value = config.exclusion_size.width
        self.exclusion_height_knob.value = config.exclusion_size.height
        self.loaded_generation = config.initial_generation
        self.update_map_preview()

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
            self.gps_tracker.reset(self.loaded_generation)
            playback_settings = self.gather_playback_settings()
            self._last_fps = playback_settings.snapshots_per_second
            self._last_mode = playback_settings.mode.value
            config = self.gather_world_config()
            self.loaded_generation = 1
            self.loaded_genomes = None
            self.last_snapshot = None

            self.process = Process(
                target=run_simulation_worker,
                args=(
                    config,
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
            # Drain remaining snapshots from worker queue upon stop to capture
            # the final match epoch and preserve latest telemetry for saving/inspection.
            while not self.snapshot_queue.empty():
                try:
                    self.last_snapshot = self.snapshot_queue.get_nowait()
                except queue.Empty:
                    break
            self.gps_tracker.reset()

        self.is_running = not self.is_running
        self.sim_button.label = "Stop simulation" if self.is_running else "Start simulation"
        self._update_active_items()
        return None

    def update(self, dt: float, screen_size: Size) -> None:
        super().update(dt, screen_size)
        if self.status_message_timer > 0.0:
            self.status_message_timer -= dt
            if self.status_message_timer <= 0.0:
                self.status_message = ""
        self.champions_knob.max_value = float(self.entities_knob.value)
        self.champions_knob.value = min(self.champions_knob.value, self.champions_knob.max_value)

        self.exclusion_blinker.tick(dt)
        if not self.snapshot_queue.empty():
            self.last_snapshot = self.snapshot_queue.get()
            self.gps_tracker.update(self.last_snapshot.generation)

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
        if self.status_message:
            screen.draw_text(
                x=35,
                y=status_y,
                text=f"[!] {self.status_message}",
                fg_color=Color(255, 230, 100),
            )

        x_start, y_start = 55, 3
        if self.last_snapshot and self.is_running:
            snapshot = self.last_snapshot
            snapshot.tilemap.draw(screen, x_start, y_start)
            for team in snapshot.teams:
                for gladiator in team:
                    gladiator.draw(screen, x_start, y_start)

            if self.gps_tracker.rate > 0 and mode == Mode.SIMULATION:
                gps_suffix = f" ({format_compact(self.gps_tracker.rate)} gen/s)"
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
        else:
            self.map_preview.draw(screen, x_start, y_start)
            if self.exclusion_blink_toggle.value and self.exclusion_blinker.is_visible:
                exclusion_width = int(self.exclusion_width_knob.value)
                exclusion_height = int(self.exclusion_height_knob.value)
                if exclusion_width > 0 and exclusion_height > 0:
                    exclusion_rect = Rect.from_center(
                        center_x=x_start + ARENA_WIDTH // 2,
                        center_y=y_start + ARENA_HEIGHT // 2,
                        width=exclusion_width,
                        height=exclusion_height,
                    )
                    screen.fill_rect(exclusion_rect, char="x", fg_color=Color(255, 60, 60))
