"""
Configuration constants and global presets for the tactical arena scene.
Provides arena grid dimensions, zoom scaling configurations, and genome parameters.
"""

ARENA_WIDTH: int = 41
ARENA_HEIGHT: int = 21

ZOOM_SCALES: list[tuple[int, int]] = [
    (1, 1),
    (2, 1),
    (2, 2),
    (4, 2),
]

GENOME_SIZE: int = 64
