"""
Domain data transfer objects and state models for the tactical Arena simulation.
Consolidates tournament configuration, IPC snapshots, telemetries, and disk saves.
"""
from dataclasses import dataclass
from enum import StrEnum
import time

from sanctuary.core.clock import Timer
from sanctuary.core.geometry import Size

from .config import (
    BEST_PER_GENERATION,
    DEFAULT_ENTITIES_PER_TEAM,
    DEFAULT_MAP,
    EXCLUSION_HEIGHT,
    EXCLUSION_WIDTH,
    GPS_METRICS_INTERVAL,
    MAX_GENERATION_TURNS,
    MUTATION_RATE_PERCENT,
)
from .gladiator import Gladiator
from .tile_map import TileMap


class Mode(StrEnum):
    """Pacing mode governing simulation thread execution velocity."""
    SIMULATION = "Simulation"
    THEATRE = "Theatre"
    PAUSE = "Pause"


@dataclass(slots=True, frozen=True)
class PlaybackSettings:
    """Dynamic pacing parameters controlled in real-time from the UI."""
    snapshots_per_second: float
    mode: Mode


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
    """Configurable execution parameters for tournament genesis and gladiator lifecycle."""
    entities_per_team: int = DEFAULT_ENTITIES_PER_TEAM
    map: str = DEFAULT_MAP
    max_turns: int = MAX_GENERATION_TURNS
    best_per_generation: int = BEST_PER_GENERATION
    mutation_rate_percent: float = MUTATION_RATE_PERCENT
    exclusion_size: Size = Size(EXCLUSION_WIDTH, EXCLUSION_HEIGHT)
    initial_generation: int = 1
    initial_genomes: dict[str, list[list[int]]] | None = None


@dataclass(slots=True, frozen=True)
class SimulationSave:
    """Disk-serialized simulation state bundling world hyperparameters and champion dynasties."""
    version: int
    world_config: WorldConfig
    generation: int
    created_at: str
    red_genomes: list[list[int]]
    blue_genomes: list[list[int]]


@dataclass
class GpsTracker:
    """Tracks generation-per-second computational velocity."""
    interval: float = GPS_METRICS_INTERVAL
    rate: float = 0.0
    _last_time: float = 0.0
    _last_generation: int = 1

    def reset(self, initial_generation: int = 1) -> None:
        """Resets the velocity counter and baseline timestamp."""
        self.rate = 0.0
        self._last_time = time.perf_counter()
        self._last_generation = initial_generation

    def update(self, current_generation: int) -> None:
        """Samples current generation and recalculates rolling rate upon interval expiration."""
        now = time.perf_counter()
        elapsed = now - self._last_time
        if elapsed >= self.interval:
            delta = current_generation - self._last_generation
            self.rate = max(0.0, delta / elapsed)
            self._last_time = now
            self._last_generation = current_generation


class BlinkIndicator:
    """Encapsulates periodic visibility toggling driven by a clock Timer."""
    timer: Timer
    is_visible: bool

    def __init__(self, interval: float = 0.5) -> None:
        self.timer = Timer(interval)
        self.is_visible = True

    def tick(self, dt: float) -> bool:
        """Advances internal timer and toggles visibility state upon expiration."""
        if self.timer.tick(dt):
            self.is_visible = not self.is_visible
            return True
        return False

    def reset(self) -> None:
        """Restores indicator to visible baseline and resets timer."""
        self.timer.reset()
        self.is_visible = True

