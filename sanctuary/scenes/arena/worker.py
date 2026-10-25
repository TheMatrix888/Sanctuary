"""
Arena Simulation Worker — Background multiprocessing engine for evolutionary bytecode gladiators.
Manages isolated tournament execution, genetic lifecycle, and state snapshot IPC.
"""
import queue
import time
from dataclasses import dataclass
from enum import StrEnum
from multiprocessing import Queue
from multiprocessing.synchronize import Event as EventType
from random import randint, random, sample

from sanctuary.core.geometry import Point, Rect

from .config import (
    AMBIENT_HP_DRAIN,
    ARENA_HEIGHT,
    ARENA_WIDTH,
    EXCLUSION_HEIGHT,
    EXCLUSION_WIDTH,
    BEST_PER_GENERATION,
    BLOOD_FLOOR_HEAL_HP,
    BLOOD_FLOOR_SCORE,
    CENTER_APPROACH_MULTIPLIER,
    GENOME_SIZE,
    MAX_GENERATION_TURNS,
    MAX_VM_ACTIONS_PER_TICK,
    MUTATION_RATE_PERCENT,
    SURVIVAL_BONUS,
)
from .generators import ARENA_PRESETS
from .gladiator import Gladiator, create_gladiator
from .tile_map import TileMap
from .tiles import BLOOD_FLOOR

HALF_WIDTH = ARENA_WIDTH // 2
HALF_HEIGHT = ARENA_HEIGHT // 2

CENTER_EXCLUSION = Rect.from_center(
    center_x=HALF_WIDTH,
    center_y=HALF_HEIGHT,
    width=EXCLUSION_WIDTH,
    height=EXCLUSION_HEIGHT,
)

QUADRANTS: tuple[Rect, ...] = (
    Rect.from_corners(1, 1, HALF_WIDTH - 1, HALF_HEIGHT - 1),  # 0: Top-Left
    Rect.from_corners(HALF_WIDTH, 1, ARENA_WIDTH - 2, HALF_HEIGHT - 1),  # 1: Top-Right
    Rect.from_corners(HALF_WIDTH, HALF_HEIGHT, ARENA_WIDTH - 2, ARENA_HEIGHT - 2),  # 2: Bottom-Right
    Rect.from_corners(1, HALF_HEIGHT, HALF_WIDTH - 1, ARENA_HEIGHT - 2),  # 3: Bottom-Left
)

MOVE_DELTAS: tuple[tuple[int, int], ...] = (
    (0, 1),  # 0: Down  (y + 1)
    (-1, 0),  # 1: Left  (x - 1)
    (0, -1),  # 2: Up    (y - 1)
    (1, 0),  # 3: Right (x + 1)
)


@dataclass(slots=True, frozen=True)
class GenerationRecord:
    """Historical benchmark record tracking generation longevity and survivability."""
    generation: int
    turns: int
    survivors: int


@dataclass(slots=True, frozen=True)
class Snapshot:
    """Inter-process state telemetry sent from simulation worker to UI screen."""
    teams: list[list[Gladiator]]
    tilemap: TileMap
    turn: int
    generation: int
    record: GenerationRecord


@dataclass(slots=True, frozen=True)
class WorldConfig:
    """Configurable execution parameters for tournament and visual pacing."""
    entities_per_team: int
    map: str
    max_turns: int = MAX_GENERATION_TURNS
    best_per_generation: int = BEST_PER_GENERATION
    mutation_rate_percent: float = MUTATION_RATE_PERCENT
    exclusion_width: int = EXCLUSION_WIDTH
    exclusion_height: int = EXCLUSION_HEIGHT

class Mode(StrEnum):
    SIMULATION = "Simulation"
    THEATRE = "Theatre"
    PAUSE = "Pause"


@dataclass(slots=True, frozen=True)
class PlaybackSettings:
    snapshots_per_second: float
    mode: Mode


class SimulationWorker:
    """
    Headless background simulation engine managing the genetic lifecycle,
    bytecode virtual machine execution, and cross-generation reproduction.
    """
    config: WorldConfig
    playback_settings: PlaybackSettings
    tilemap: TileMap
    _quadrant_pools: tuple[list[Point], ...]
    red_team: list[Gladiator]
    blue_team: list[Gladiator]
    snapshot_interval: float
    next_snapshot: float
    playback_settings_queue: Queue
    snapshot_queue: Queue
    stop_event: EventType
    running: bool
    generation: int
    turn: int
    max_turns: int
    dead_gladiators: int
    record: GenerationRecord

    def __init__(
            self,
            world_config: WorldConfig,
            playback_settings: PlaybackSettings,
            playback_settings_queue: Queue,
            snapshot_queue: Queue,
            stop_event: EventType,
    ) -> None:
        self.playback_settings_queue = playback_settings_queue
        self.snapshot_queue = snapshot_queue
        self.stop_event = stop_event
        self.running = False
        self.reset(world_config, playback_settings)

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
            for _ in range(self.config.entities_per_team)
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
            for _ in range(self.config.entities_per_team)
        ]

    def _build_tiles_pool(self, quadrant: Rect, center_exclusion: Rect) -> list[Point]:
        """Extracts walkable floor cells in a quadrant excluding the central exclusion zone."""
        has_exclusion = center_exclusion.width > 0 and center_exclusion.height > 0
        return [
            point
            for point in quadrant
            if (not has_exclusion or point not in center_exclusion)
            and self.tilemap.is_walkable(point.x, point.y)
        ]

    def position_teams(self) -> None:
        """Samples non-blood walkable floor cells in opposing quadrant corners and positions gladiators."""
        red_quadrant = randint(0, 3)
        blue_quadrant = (red_quadrant + 2) % 4

        red_pool = self._quadrant_pools[red_quadrant]
        blue_pool = self._quadrant_pools[blue_quadrant]

        entities_count = self.config.entities_per_team
        red_spawns = sample(red_pool, k=min(entities_count, len(red_pool)))
        blue_spawns = sample(blue_pool, k=min(entities_count, len(blue_pool)))

        for gladiator, spawn in zip(self.red_team + self.blue_team, red_spawns + blue_spawns):
            gladiator.set_position(spawn.x, spawn.y)

    def new_generation(self) -> None:
        """Executes epoch transition: evaluates fitness, selects champions, reproduces, and mutates."""
        center_x = ARENA_WIDTH // 2
        center_y = ARENA_HEIGHT // 2

        # 1. Final epoch scoring (survival and center proximity benchmarks)
        survivors = 0
        for gladiator in self.red_team + self.blue_team:
            if gladiator.hp > 0:
                gladiator.score += SURVIVAL_BONUS
                survivors += 1

            spawn_dist = abs(gladiator.spawn_x - center_x) + abs(gladiator.spawn_y - center_y)
            approach_progress = max(0, spawn_dist - gladiator.min_distance)
            gladiator.score += approach_progress * CENTER_APPROACH_MULTIPLIER

            gladiator.resurrect()

        # 2. Elitist selection: sort teams by achieved score
        self.red_team.sort(key=lambda g: g.score, reverse=True)
        self.blue_team.sort(key=lambda g: g.score, reverse=True)

        k_champions = min(self.config.best_per_generation, len(self.red_team))
        red_champion_genomes = [g.genome.copy() for g in self.red_team[:k_champions]]
        blue_champion_genomes = [g.genome.copy() for g in self.blue_team[:k_champions]]

        # 3. Reproduction: cycle champion genomes and reset per-round score
        def reproduce(team: list[Gladiator], champion_genomes: list[list[int]]) -> None:
            for i, gladiator in enumerate(team):
                parent_genome = champion_genomes[i % len(champion_genomes)]
                gladiator.genome = parent_genome.copy()
                gladiator.score = 0
                gladiator.pc = 0

        reproduce(self.red_team, red_champion_genomes)
        reproduce(self.blue_team, blue_champion_genomes)

        # 4. Uniform per-gene point mutations: preserve top champion (index 0) intact
        mutation_probability = self.config.mutation_rate_percent / 100.0
        if mutation_probability > 0.0:
            def mutate(team: list[Gladiator]) -> None:
                for gladiator in team[1:]:
                    genome = gladiator.genome
                    for gene_index in range(GENOME_SIZE):
                        if random() < mutation_probability:
                            genome[gene_index] = randint(0, GENOME_SIZE - 1)

            mutate(self.red_team)
            mutate(self.blue_team)

        # 5. Record generation records and reset telemetry
        if self.turn > self.record.turns or (self.turn == self.record.turns and survivors > self.record.survivors):
            self.record = GenerationRecord(
                generation=self.generation,
                turns=self.turn,
                survivors=survivors,
            )

        self.dead_gladiators = 0
        self.turn = 0
        self.generation += 1
        self.position_teams()

    def reset(self, config: WorldConfig, playback_settings: PlaybackSettings) -> None:
        """Resets the simulation world, generators, and state telemetry."""
        self.config = config
        self.playback_settings = playback_settings
        generator = ARENA_PRESETS[config.map]
        self.tilemap = generator(ARENA_WIDTH, ARENA_HEIGHT)
        center_exclusion = Rect.from_center(
            center_x=HALF_WIDTH,
            center_y=HALF_HEIGHT,
            width=config.exclusion_width,
            height=config.exclusion_height,
        )
        self._quadrant_pools = tuple(self._build_tiles_pool(quadrant, center_exclusion) for quadrant in QUADRANTS)

        self.create_teams()
        self.position_teams()
        self.generation = 1
        self.turn = 0
        self.record = GenerationRecord(generation=1, turns=0, survivors=0)
        self.dead_gladiators = 0
        self.max_turns = self.config.max_turns

        self.snapshot_interval = 1.0 / max(1.0, playback_settings.snapshots_per_second)
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
        all_dead = self.dead_gladiators >= self.config.entities_per_team * 2
        if self.turn >= self.max_turns or all_dead:
            self.new_generation()

    def send_snapshot(self) -> None:
        """Pushes current simulation frame to UI consumer queue, dropping stale frames."""
        snapshot = Snapshot(
            teams=[self.red_team, self.blue_team],
            tilemap=self.tilemap,
            turn=self.turn,
            generation=self.generation,
            record=self.record,
        )
        if self.snapshot_queue.full():
            try:
                self.snapshot_queue.get_nowait()
            except queue.Empty:
                pass
        try:
            self.snapshot_queue.put_nowait(snapshot)
        except queue.Full:
            pass

    def _poll_playback_settings(self) -> None:
        """Drains pending playback settings from the queue and updates interval."""
        updated = False
        while not self.playback_settings_queue.empty():
            try:
                self.playback_settings = self.playback_settings_queue.get_nowait()
                updated = True
            except queue.Empty:
                break
        if updated:
            self.snapshot_interval = 1.0 / max(1.0, self.playback_settings.snapshots_per_second)

    def run(self) -> None:
        """Child process execution loop with mode-dependent pacing."""
        self.running = True
        self.next_snapshot = time.perf_counter()

        while self.running and not self.stop_event.is_set():
            mode = self.playback_settings.mode

            if mode is Mode.SIMULATION:
                self.update()
                now = time.perf_counter()
                if now >= self.next_snapshot:
                    self._poll_playback_settings()
                    self.send_snapshot()
                    self.next_snapshot = now + self.snapshot_interval

            elif mode is Mode.THEATRE:
                self.update()
                self.send_snapshot()
                self._poll_playback_settings()

                time_left = self.next_snapshot - time.perf_counter()
                if time_left > 0:
                    time.sleep(time_left)
                self.next_snapshot = time.perf_counter() + self.snapshot_interval

            elif mode is Mode.PAUSE:
                self._poll_playback_settings()
                time.sleep(0.02)
                self.next_snapshot = time.perf_counter()

            else:
                raise ValueError(f"Unsupported simulation mode: {mode}")


def run_simulation_worker(
    world_config: WorldConfig,
    playback_settings: PlaybackSettings,
    playback_settings_queue: Queue,
    snapshot_queue: Queue,
    stop_event: EventType,
) -> None:
    """Entrypoint executed in the isolated background child process."""
    worker = SimulationWorker(
        world_config=world_config,
        playback_settings=playback_settings,
        playback_settings_queue=playback_settings_queue,
        snapshot_queue=snapshot_queue,
        stop_event=stop_event,
    )
    worker.run()
