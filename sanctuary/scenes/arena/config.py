"""
Configuration constants and global presets for the tactical arena scene.
Provides arena grid dimensions, zoom scaling configurations, and genetic simulation parameters.
"""

# Spatial Grid Dimensions
ARENA_WIDTH: int = 61
ARENA_HEIGHT: int = 31

ZOOM_SCALES: list[tuple[int, int]] = [
    (1, 1),
    (2, 1),
    (2, 2),
    (4, 2),
]

# Genetic VM & Genome
GENOME_SIZE: int = 64
MAX_VM_ACTIONS_PER_TICK: int = 15

# Evolution & Tournament Hyperparameters
BEST_PER_GENERATION: int = 4
MUTATION_RATE_PERCENT: int = 8
MUTATION_GENES_COUNT: int = 3
MAX_GENERATION_TURNS: int = 500

# Scoring & Environmental Multipliers
BLOOD_FLOOR_HEAL_HP: int = 2
BLOOD_FLOOR_SCORE: int = 10
AMBIENT_HP_DRAIN: int = 1
SURVIVAL_BONUS: int = 200
CENTER_APPROACH_MULTIPLIER: int = 5
