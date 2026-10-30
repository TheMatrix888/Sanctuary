"""
Configuration constants and global presets for the tactical arena scene.
Provides arena grid dimensions, zoom scaling configurations, and genetic simulation parameters.
"""

from sanctuary.core.geometry import Point
from .generators import ARENA_PRESETS

# Spatial Grid Dimensions
ARENA_WIDTH: int = 61
ARENA_HEIGHT: int = 31

# Primary Arena Viewport Origin (Unified SVoT Alignment)
ARENA_ORIGIN: Point = Point(x=55, y=3)

# Central Exclusion Zone (Anti-Camp Buffer)
EXCLUSION_WIDTH: int = ARENA_WIDTH // 3
EXCLUSION_HEIGHT: int = ARENA_HEIGHT // 3

ZOOM_SCALES: list[tuple[int, int]] = [
    (1, 1),
    (2, 1),
    (2, 2),
    (4, 2),
]

# Genetic VM & Genome
GENOME_SIZE: int = 64
MAX_VM_ACTIONS_PER_TICK: int = 15

# Default World & Match Settings
DEFAULT_ENTITIES_PER_TEAM: int = 10
DEFAULT_MAP: str = next(iter(ARENA_PRESETS.keys()))

# Evolution & Tournament Hyperparameters
BEST_PER_GENERATION: int = 4
MUTATION_RATE_PERCENT: float = 2.0
MAX_GENERATION_TURNS: int = 200

# Scoring & Environmental Multipliers
BLOOD_FLOOR_HEAL_HP: int = 2
BLOOD_FLOOR_SCORE: int = 10
AMBIENT_HP_DRAIN: int = 1
SURVIVAL_BONUS: int = 200
CENTER_APPROACH_MULTIPLIER: int = 5

# Telemetry & Pacing
GPS_METRICS_INTERVAL: float = 1.0

# Background Process Identifier
ARENA_SIMULATION_PROCESS_NAME: str = "arena_simulation"
