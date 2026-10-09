"""
Arena package: tactical procedural combat sandbox, discrete raytracing, and map presets.
"""
from sanctuary.scenes.arena.generators import (
    ARENA_PRESETS,
    ArenaPreset,
    generate_colosseum,
    generate_concentric_bastions,
    generate_greek_amphitheater,
    generate_proving_ground,
    generate_sierpinski_ruins,
    generate_tectonic_chasm,
)
from sanctuary.scenes.arena.map import ArenaMap
from sanctuary.scenes.arena.state import ARENA_HEIGHT, ARENA_WIDTH, Arena, Entity
from sanctuary.scenes.arena.tiles import (
    BLOOD_FLOOR,
    CHASM,
    FLOOR,
    WALL,
    Tile,
    get_tile_render,
)

__all__ = [
    "ARENA_HEIGHT",
    "ARENA_WIDTH",
    "ARENA_PRESETS",
    "Arena",
    "ArenaMap",
    "ArenaPreset",
    "BLOOD_FLOOR",
    "CHASM",
    "Entity",
    "FLOOR",
    "Tile",
    "WALL",
    "generate_colosseum",
    "generate_concentric_bastions",
    "generate_greek_amphitheater",
    "generate_proving_ground",
    "generate_sierpinski_ruins",
    "generate_tectonic_chasm",
    "get_tile_render",
]
