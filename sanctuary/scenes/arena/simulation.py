"""
Arena Simulation Form State — Parameter inspector and genetic tournament configuration.
"""
import time
from dataclasses import dataclass
from multiprocessing import Process, Queue, Event
from multiprocessing.synchronize import Event as EventType

from sanctuary.core.geometry import Size
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Pop
from sanctuary.scenes.arena.generators import ARENA_PRESETS
from sanctuary.scenes.arena.state import TileMap, ARENA_WIDTH, ARENA_HEIGHT, EMPTY
from sanctuary.scenes.arena.tiles import Texture, BLOOD_FLOOR, RED_GLADIATOR_TEXTURE, BLUE_GLADIATOR_TEXTURE, FLOOR
from sanctuary.scenes.arena.entities import Entity
from sanctuary.ui.form import FormState
from sanctuary.ui.widgets import Button, ChoiceKnob, Knob

from random import randint, sample



def act_move(gladiator: "Gladiator", dx: int = 0, dy: int = 0) -> bool:
    """Moves gladiator by (dx, dy). Terminal action ending turn."""
    gladiator.entity.x += dx
    gladiator.entity.y += dy
    return True


def act_look(gladiator: "Gladiator", dx: int = 0, dy: int = 0) -> bool:
    """Sensor: checks obstacle ahead. Non-terminal action."""
    # If obstacle/enemy ahead — advance PC by 2, if clear — advance by 1.
    return False


def act_current_tile(gladiator: "Gladiator") -> int:
    """Sensor: inspects current cell tile prototype."""
    return 0


class Gladiator:
    genome: list[int]
    genome_index: int
    entity: Entity

    def __init__(self, texture: Texture) -> None:
        self.genome = [randint(0, 64) for _ in range(64)]
        self.genome_index = 0
        self.entity = Entity(
            x=0,
            y=0,
            texture=texture
        )

    def turn(self) -> None:
        gene = self.genome[self.genome_index]
        self.genome_index = (self.genome_index + 1) % len(self.genome)




def generate_team(gladiators: int, team: str):
    if team == "red":
        texture = RED_GLADIATOR_TEXTURE
    else:
        texture = BLUE_GLADIATOR_TEXTURE

    return [Gladiator(texture) for _ in range(gladiators)]


@dataclass(slots=True, frozen=True)
class Snapshot:
    teams: list[list[Gladiator]]
    tilemap: TileMap


@dataclass(slots=True, frozen=True)
class SimulationSettings:
    entities_per_team: int
    snapshots_per_second: float
    map: str


class SimulationWorker:
    settings: SimulationSettings
    tilemap: TileMap
    red_team: list[Gladiator]
    blue_team: list[Gladiator]
    snapshot_time: float
    next_snapshot: float
    queue: Queue
    stop_event: EventType
    running: bool

    def __init__(self, queue: Queue, stop_event: EventType, settings: SimulationSettings) -> None:
        self.queue = queue
        self.stop_event = stop_event
        self.reset(settings)

    def position_teams(self) -> None:
        half_width = ARENA_WIDTH // 2
        half_height = ARENA_HEIGHT // 2

        def tiles_pool(x_min: int, x_max: int, y_min: int, y_max: int) -> list[tuple[int, int]]:
            # Collect only walkable non-blood floor cells within the target quadrant bounds
            return [
                (x, y)
                for y in range(y_min, y_max + 1)
                for x in range(x_min, x_max + 1)
                if self.tilemap.is_walkable(x, y) and self.tilemap.get_tile(x, y) is not BLOOD_FLOOR
            ]

        # 1. Spawn candidate pools for opposing quadrant corners (top-left vs bottom-right)
        red_pool = tiles_pool(1, half_width - 1, 1, half_height - 1)
        blue_pool = tiles_pool(half_width, ARENA_WIDTH - 2, half_height, ARENA_HEIGHT - 2)

        # random.sample guarantees collision-free unique spawn coordinates without retries
        red_spawns = sample(red_pool, k=min(len(self.red_team), len(red_pool)))
        for gladiator, (x, y) in zip(self.red_team, red_spawns):
            gladiator.entity.x, gladiator.entity.y = x, y
        blue_spawns = sample(blue_pool, k=min(len(self.blue_team), len(blue_pool)))
        for gladiator, (x, y) in zip(self.blue_team, blue_spawns):
            gladiator.entity.x, gladiator.entity.y = x, y

    def reset(self, settings: SimulationSettings) -> None:
        self.settings = settings

        generator = ARENA_PRESETS[settings.map]
        self.tilemap = generator(ARENA_WIDTH, ARENA_HEIGHT)

        self.red_team = generate_team(settings.entities_per_team, "red")
        self.blue_team = generate_team(settings.entities_per_team, "blue")
        self.position_teams()

        self.snapshot_time = 1.0 / settings.snapshots_per_second
        self.next_snapshot = time.perf_counter()

    def update(self) -> None:
        gladiators = [gladiator for pair in zip(self.red_team, self.blue_team) for gladiator in pair]
        for gladiator in gladiators:
            gladiator.turn()

    def send_snapshot(self) -> None:
        try:
            if self.queue.full():
                try:
                    self.queue.get_nowait()
                except Exception:
                    pass
            self.queue.put_nowait(Snapshot(teams=[self.red_team, self.blue_team], tilemap=self.tilemap))
        # TODO: Replace bare 'except Exception: pass' with explicit error handling or documented non-blocking IPC rationale.
        except Exception:
            pass

    def run(self) -> None:
        self.running = True
        while self.running and not self.stop_event.is_set():
            self.update()
            if time.perf_counter() >= self.next_snapshot:
                self.send_snapshot()
                self.next_snapshot = time.perf_counter() + self.snapshot_time


def run_simulation_worker(queue: Queue, stop_event: EventType, settings: SimulationSettings) -> None:
    """Entrypoint executed in the isolated background child process."""
    worker = SimulationWorker(queue, stop_event, settings)
    worker.run()


class ArenaSimulation(FormState):
    """
    Inspector and tournament configurator state for the evolutionary arena simulation.
    Allows configuring gladiator entity counts, snapshot rates, maps, and runtime execution.
    """
    is_running: bool
    sim_button: Button
    process: Process | None
    queue: Queue
    stop_event: EventType
    last_snapshot: Snapshot | None

    def __init__(self) -> None:
        self.is_running = False
        self.queue = Queue(maxsize=2)
        self.stop_event = Event()
        self.process = None
        self.last_snapshot = None

        self.sim_button = Button(
            label="Start simulation",
            callback=self._toggle_simulation,
        )

        items = [
            self.sim_button,

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
                label="Load genome [WIP]",
                action=None,
            ),
            Button(
                label="Save genome [WIP]",
                action=None,
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

    def gather_settings(self) -> SimulationSettings:
        # TODO: Refactor index-based item lookup into named keys / declarative bindings in FormState.
        return SimulationSettings(
            entities_per_team=int(self.items[1].value),
            snapshots_per_second=self.items[2].value,
            map=self.items[3].current_value
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
        return None

    def update(self, dt: float, screen_size: Size) -> None:
        super().update(dt, screen_size)
        if not self.queue.empty():
            self.last_snapshot = self.queue.get()

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

        if self.last_snapshot:
            # Reused from arena.py — extract into shared TileMap renderer with scale support.
            x_start, y_start = 50, 3
            tilemap = self.last_snapshot.tilemap
            for y in range(tilemap.height):
                for x in range(tilemap.width):
                    tile = tilemap.get_tile(x, y)
                    if tile != EMPTY:
                        screen_x = x_start + x
                        screen_y = y_start + y
                        surface = tile.texture.get_surface()
                        screen.draw_surface(screen_x, screen_y, surface)
            for team in self.last_snapshot.teams:
                for gladiator in team:
                    screen_x = x_start + gladiator.entity.x
                    screen_y = y_start + gladiator.entity.y
                    surface = gladiator.entity.texture.get_surface()
                    screen.draw_surface(screen_x, screen_y, surface)
