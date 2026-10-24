"""
Arena Simulation Worker — Background multiprocessing engine for evolutionary bytecode gladiators.
Manages isolated tournament execution, genetic lifecycle, and state snapshot IPC.
"""
import queue
import time
from dataclasses import dataclass
from multiprocessing import Queue
from multiprocessing.synchronize import Event as EventType
from random import randint, sample

from sanctuary.core.geometry import Point

from .config import (
    AMBIENT_HP_DRAIN,
    ARENA_HEIGHT,
    ARENA_WIDTH,
    BEST_PER_GENERATION,
    BLOOD_FLOOR_HEAL_HP,
    BLOOD_FLOOR_SCORE,
    CENTER_APPROACH_MULTIPLIER,
    GENOME_SIZE,
    MAX_GENERATION_TURNS,
    MAX_VM_ACTIONS_PER_TICK,
    MUTATION_GENES_COUNT,
    MUTATION_RATE_PERCENT,
    SURVIVAL_BONUS,
)
from .generators import ARENA_PRESETS
from .gladiator import Gladiator, create_gladiator
from .tile_map import TileMap
from .tiles import BLOOD_FLOOR

HALF_WIDTH = ARENA_WIDTH // 2
HALF_HEIGHT = ARENA_HEIGHT // 2

QUADRANT_BOUNDS = (
    (1, HALF_WIDTH - 1, 1, HALF_HEIGHT - 1),                        # 0: Top-Left
    (HALF_WIDTH, ARENA_WIDTH - 2, 1, HALF_HEIGHT - 1),              # 1: Top-Right
    (HALF_WIDTH, ARENA_WIDTH - 2, HALF_HEIGHT, ARENA_HEIGHT - 2),   # 2: Bottom-Right
    (1, HALF_WIDTH - 1, HALF_HEIGHT, ARENA_HEIGHT - 2),             # 3: Bottom-Left
)

MOVE_DELTAS: tuple[tuple[int, int], ...] = (
    (0, 1),   # 0: Down  (y + 1)
    (-1, 0),  # 1: Left  (x - 1)
    (0, -1),  # 2: Up    (y - 1)
    (1, 0),   # 3: Right (x + 1)
)


@dataclass(slots=True, frozen=True)
class Snapshot:
    """Inter-process state telemetry sent from simulation worker to UI screen."""
    teams: list[list[Gladiator]]
    tilemap: TileMap
    turn: int
    generation: int
    longest_generation: tuple[int, int]


@dataclass(slots=True, frozen=True)
class SimulationSettings:
    """Configurable execution parameters for tournament and visual pacing."""
    entities_per_team: int
    snapshots_per_second: float
    mode: str
    map: str


class SimulationWorker:
    """
    Headless background simulation engine managing the genetic lifecycle,
    bytecode virtual machine execution, and cross-generation reproduction.
    """
    settings: SimulationSettings
    tilemap: TileMap
    red_team: list[Gladiator]
    blue_team: list[Gladiator]
    snapshot_time: float
    next_snapshot: float
    queue: Queue
    stop_event: EventType
    running: bool
    generation: int
    turn: int
    max_turns: int
    dead_gladiators: int
    longest_generation: tuple[int, int]

    def __init__(self, snapshot_queue: Queue, stop_event: EventType, settings: SimulationSettings) -> None:
        self.queue = snapshot_queue
        self.stop_event = stop_event
        self.reset(settings)

    def create_teams(self) -> None:
        """Initializes empty gladiator pools for both factions with default metrics."""
        self.red_team = [
            create_gladiator(
                x=0,
                y=0,
                view_distance=10,
                hp=100,
                max_hp=100,
                faction="red",
            )
            for _ in range(self.settings.entities_per_team)
        ]
        self.blue_team = [
            create_gladiator(
                x=0,
                y=0,
                view_distance=10,
                hp=100,
                max_hp=100,
                faction="blue",
            )
            for _ in range(self.settings.entities_per_team)
        ]

    def position_teams(self) -> None:
        """Samples non-blood walkable floor cells in opposing quadrant corners and positions gladiators."""
        red_quadrant = randint(0, 3)
        blue_quadrant = (red_quadrant + 2) % 4

        def tiles_pool(x_min: int, x_max: int, y_min: int, y_max: int) -> list[Point]:
            return [
                Point(x, y)
                for y in range(y_min, y_max + 1)
                for x in range(x_min, x_max + 1)
                if self.tilemap.is_walkable(x, y) and self.tilemap.get_tile(x, y) is not BLOOD_FLOOR
            ]

        red_pool = tiles_pool(*QUADRANT_BOUNDS[red_quadrant])
        blue_pool = tiles_pool(*QUADRANT_BOUNDS[blue_quadrant])

        entities_count = self.settings.entities_per_team
        red_spawns = sample(red_pool, k=min(entities_count, len(red_pool)))
        blue_spawns = sample(blue_pool, k=min(entities_count, len(blue_pool)))

        for gladiator, spawn in zip(self.red_team + self.blue_team, red_spawns + blue_spawns):
            gladiator.set_position(spawn.x, spawn.y)

    def new_generation(self) -> None:
        """Executes epoch transition: evaluates fitness, selects champions, reproduces, and mutates."""
        center_x = ARENA_WIDTH // 2
        center_y = ARENA_HEIGHT // 2

        # 1. Final epoch scoring (survival and center proximity benchmarks)
        for gladiator in self.red_team + self.blue_team:
            if gladiator.hp > 0:
                gladiator.score += SURVIVAL_BONUS

            spawn_dist = abs(gladiator.spawn_x - center_x) + abs(gladiator.spawn_y - center_y)
            approach_progress = max(0, spawn_dist - gladiator.min_distance)
            gladiator.score += approach_progress * CENTER_APPROACH_MULTIPLIER

            gladiator.resurrect()

        # 2. Elitist selection: sort teams by achieved score
        self.red_team.sort(key=lambda g: g.score, reverse=True)
        self.blue_team.sort(key=lambda g: g.score, reverse=True)

        k_champions = min(BEST_PER_GENERATION, len(self.red_team))
        red_champion_genomes = [g.genome.copy() for g in self.red_team[:k_champions]]
        blue_champion_genomes = [g.genome.copy() for g in self.blue_team[:k_champions]]

        # 3. Reproduction: cycle champion genomes and reset per-round score
        for i, gladiator in enumerate(self.red_team):
            parent_genome = red_champion_genomes[i % len(red_champion_genomes)]
            gladiator.genome = parent_genome.copy()
            gladiator.score = 0
            gladiator.pc = 0

        for i, gladiator in enumerate(self.blue_team):
            parent_genome = blue_champion_genomes[i % len(blue_champion_genomes)]
            gladiator.genome = parent_genome.copy()
            gladiator.score = 0
            gladiator.pc = 0

        # 4. Point mutations: preserve top champion (index 0) intact, mutate descendants
        def mutate(team: list[Gladiator]) -> None:
            for gladiator in team[1:]:
                if randint(1, 100) <= MUTATION_RATE_PERCENT:
                    mutation_indices = sample(range(GENOME_SIZE), MUTATION_GENES_COUNT)
                    mutation_values = [randint(0, GENOME_SIZE - 1) for _ in range(MUTATION_GENES_COUNT)]
                    for idx, val in zip(mutation_indices, mutation_values):
                        gladiator.genome[idx] = val

        mutate(self.red_team)
        mutate(self.blue_team)

        # 5. Record generation records and reset telemetry
        if self.turn > self.longest_generation[1]:
            self.longest_generation = (self.generation, self.turn)

        self.dead_gladiators = 0
        self.turn = 0
        self.generation += 1
        self.position_teams()

    def reset(self, settings: SimulationSettings) -> None:
        """Resets the simulation world, generators, and state telemetry."""
        self.settings = settings
        generator = ARENA_PRESETS[settings.map]
        self.tilemap = generator(ARENA_WIDTH, ARENA_HEIGHT)

        self.create_teams()
        self.position_teams()
        self.generation = 1
        self.turn = 0
        self.longest_generation = (1, 0)
        self.dead_gladiators = 0
        self.max_turns = MAX_GENERATION_TURNS

        self.snapshot_time = 1.0 / settings.snapshots_per_second
        self.next_snapshot = time.perf_counter()

    def update(self) -> None:
        """Executes a single simulation tick across interleaved team gladiators."""
        center_x = ARENA_WIDTH // 2
        center_y = ARENA_HEIGHT // 2

        gladiators = [gladiator for pair in zip(self.red_team, self.blue_team) for gladiator in pair]
        for gladiator in gladiators:
            if gladiator.hp <= 0:
                continue

            action_budget = 0
            while action_budget < MAX_VM_ACTIONS_PER_TICK:
                gene = gladiator.current_gene

                # Opcodes 0..3: Cardinal movement
                if gene < 4:
                    dx, dy = MOVE_DELTAS[gene]
                    nx, ny = gladiator.x + dx, gladiator.y + dy
                    if self.tilemap.is_walkable(nx, ny):
                        gladiator.x, gladiator.y = nx, ny
                        gladiator.record_distance(center_x, center_y)
                        gladiator.pc = (gladiator.pc + 1) % GENOME_SIZE
                    else:
                        gladiator.pc = (gladiator.pc + 2) % GENOME_SIZE
                    action_budget += MAX_VM_ACTIONS_PER_TICK

                # Opcode 4: Rest / Stay in place
                elif gene == 4:
                    action_budget += MAX_VM_ACTIONS_PER_TICK

                # Opcode 5: Sense current floor tile (blood vs normal floor)
                elif gene == 5:
                    if self.tilemap.get_tile(gladiator.x, gladiator.y) is BLOOD_FLOOR:
                        gladiator.pc = (gladiator.pc + 1) % GENOME_SIZE
                    else:
                        gladiator.pc = (gladiator.pc + 2) % GENOME_SIZE
                    action_budget += 1

                # Opcodes 6..63: Unconditional relative jump
                else:
                    gladiator.pc = (gladiator.pc + gene) % GENOME_SIZE
                    action_budget += 1

            # Environmental reaction: sun/blood heals and rewards, ambient arena burns HP
            if self.tilemap.get_tile(gladiator.x, gladiator.y) is BLOOD_FLOOR:
                gladiator.hp = min(gladiator.max_hp, gladiator.hp + BLOOD_FLOOR_HEAL_HP)
                gladiator.score += BLOOD_FLOOR_SCORE
            else:
                gladiator.hp -= AMBIENT_HP_DRAIN

            # Death detection and corpse texture swap
            if gladiator.hp <= 0:
                gladiator.hp = 0
                gladiator.texture = gladiator.dead_texture
                self.dead_gladiators += 1

        self.turn += 1

        # Check generation end conditions
        all_dead = self.dead_gladiators >= self.settings.entities_per_team * 2
        if self.turn >= self.max_turns or all_dead:
            self.new_generation()

    def send_snapshot(self) -> None:
        """Pushes current simulation frame to UI consumer queue, dropping stale frames."""
        snapshot = Snapshot(
            teams=[self.red_team, self.blue_team],
            tilemap=self.tilemap,
            turn=self.turn,
            generation=self.generation,
            longest_generation=self.longest_generation,
        )
        if self.queue.full():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass
        try:
            self.queue.put_nowait(snapshot)
        except queue.Full:
            pass

    def run(self) -> None:
        """Child process execution loop with mode-dependent pacing."""
        self.running = True
        while self.running and not self.stop_event.is_set():
            now = time.perf_counter()
            if self.settings.mode == "Simulation":
                self.update()
            if now >= self.next_snapshot:
                self.update()
                self.send_snapshot()
                self.next_snapshot = now + self.snapshot_time
            else:
                time.sleep(0.001)


def run_simulation_worker(snapshot_queue: Queue, stop_event: EventType, settings: SimulationSettings) -> None:
    """Entrypoint executed in the isolated background child process."""
    worker = SimulationWorker(snapshot_queue, stop_event, settings)
    worker.run()
