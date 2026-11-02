"""
Arena Setup State — Parameter inspector and genetic tournament configuration.
Coordinates tournament setup, map generation, exclusion buffers, and genome persistence.
"""
from __future__ import annotations

from pathlib import Path

from sanctuary.core.formatting import format_compact
from sanctuary.core.geometry import Rect, Size
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import Commands, Pop, Push, StartProcess
from sanctuary.ui.form import FormState
from sanctuary.ui.widgets import Button, ChoiceKnob, Dropdown, Header, Knob, Spacer, Toggle

from .config import (
    ARENA_HEIGHT,
    ARENA_ORIGIN,
    ARENA_WIDTH,
    BEST_PER_GENERATION,
    DEFAULT_ENTITIES_PER_TEAM,
    EXCLUSION_HEIGHT,
    EXCLUSION_WIDTH,
    MAX_GENERATION_TURNS,
    MUTATION_RATE_PERCENT,
)
from .generators import ARENA_PRESETS
from .models import (
    BlinkIndicator,
    Snapshot,
    WorldConfig,
)
from .persistence import (
    SAVES_DIR,
    list_simulation_saves,
    load_simulation,
    save_simulation,
)
from .running import ArenaRunningState
from .tile_map import TileMap


class ArenaSetupState(FormState):
    """
    Inspector and tournament configurator state for the evolutionary arena simulation.
    Allows configuring gladiator entity counts, mutation rates, procedural maps, and exclusion buffers.
    """
    # ui
    start_button: Button
    setup_header: Header
    tournament_header: Header
    entities_knob: Knob
    map_knob: ChoiceKnob
    exclusion_width_knob: Knob
    exclusion_height_knob: Knob
    exclusion_blink_toggle: Toggle
    exclusion_blinker: BlinkIndicator
    max_turns_knob: Knob
    champions_knob: Knob
    mutation_rate_knob: Knob
    load_dropdown: Dropdown
    save_button: Button
    back_button: Button
    # TODO divide into categories using comments (in all classes)
    loaded_genomes: dict[str, list[list[int]]] | None
    loaded_generation: int
    status_message: str
    status_message_timer: float
    current_map: str
    map_preview: TileMap
    saves_dir: Path
    running_state: ArenaRunningState | None
    last_snapshot: Snapshot | None

    def __init__(self, saves_dir: Path = SAVES_DIR) -> None:
        self.saves_dir = saves_dir
        self.running_state = None
        self.last_snapshot = None
        self.exclusion_blinker = BlinkIndicator(0.5)
        self.loaded_genomes = None
        self.loaded_generation = 1
        self.status_message = ""
        self.status_message_timer = 0.0

        self._build_widgets()

        super().__init__(
            title="Arena Simulation",
            items=[
                self.start_button,
                Spacer(),
                self.setup_header,
                self.entities_knob,
                self.map_knob,
                self.exclusion_blink_toggle,
                self.exclusion_width_knob,
                self.exclusion_height_knob,
                Spacer(),
                self.tournament_header,
                self.max_turns_knob,
                self.champions_knob,
                self.mutation_rate_knob,
                Spacer(),
                self.load_dropdown,
                self.save_button,
                self.back_button,
            ],
            on_cancel=Pop(),
        )

        self.update_map_preview()

    def _build_widgets(self) -> None:
        """Instantiates declarative form widgets, knobs, and section headers."""
        self.start_button = Button("Start simulation", action=self._on_start_button)
        self.setup_header = Header("--- Simulation Setup ---", color=Color(245, 110, 115))
        self.tournament_header = Header("--- Tournament & Evolution ---", color=Color(255, 180, 80))

        self.entities_knob = Knob.integer(
            "Entities per team",
            value=DEFAULT_ENTITIES_PER_TEAM,
            min_value=1,
            max_value=100,
            suffix="entities",
        )
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
        self.save_button = Button("Save latest snapshot genome [None]", action=self._on_save_genome)
        self.back_button = Button("Back", action=Pop())

    def _on_start_button(self) -> Commands:
        """Pushes active running state or initializes fresh tournament worker."""
        if self.running_state is not None:
            return Push(self.running_state)

        config = self.gather_world_config()
        self.loaded_generation = 1
        self.loaded_genomes = None
        self.last_snapshot = None

        running = ArenaRunningState(
            setup_state=self,
            world_config=config,
            saves_dir=self.saves_dir,
        )
        self.running_state = running
        proc = running.create_worker_process()
        self.start_button.label = "View active simulation"
        return StartProcess(proc), Push(running)

    def _on_save_genome(self) -> None:
        """Serializes last captured snapshot teams into a timestamped genome bundle."""
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

            count = len(save.red_genomes)
            self.status_message = f"Loaded {path.name} [{count} champions, Gen {format_compact(save.generation)}]"
            self.status_message_timer = 4.0
        except Exception as error:
            self.status_message = f"Load failed: {error}"
            self.status_message_timer = 4.0

    def update_map_preview(self) -> None:
        """Regenerates the procedural map tilemap matching the active selection."""
        self.current_map = self.map_knob.value
        self.map_preview = ARENA_PRESETS[self.current_map](ARENA_WIDTH, ARENA_HEIGHT)

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

    def update(self, dt: float, screen_size: Size) -> None:
        super().update(dt, screen_size)
        if self.status_message_timer > 0.0:
            self.status_message_timer -= dt
            if self.status_message_timer <= 0.0:
                self.status_message = ""

        self.champions_knob.max_value = float(self.entities_knob.value)
        self.champions_knob.value = min(self.champions_knob.value, self.champions_knob.max_value)
        self.exclusion_blinker.tick(dt)

        if self.current_map != self.map_knob.value:
            self.update_map_preview()

        if self.running_state is not None:
            self.start_button.label = "View active simulation"
        else:
            self.start_button.label = "Start simulation"

        if self.last_snapshot is not None:
            self.save_button.label = f"Save latest snapshot genome (Gen {format_compact(self.last_snapshot.generation)})"
        else:
            self.save_button.label = "Save latest snapshot genome [None]"

    def draw(self, screen: Screen) -> None:
        super().draw(screen)

        status_y = screen.size.rows - 2
        if self.running_state is not None:
            status_badge = "[RUNNING IN BACKGROUND]"
            status_fg = Color(80, 255, 120)
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

        x_start, y_start = ARENA_ORIGIN.x, ARENA_ORIGIN.y
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
