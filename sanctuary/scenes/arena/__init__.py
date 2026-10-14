"""
Arena package: tactical procedural combat sandbox, discrete raytracing, and map presets.
"""
from sanctuary.scenes.arena.entities import (
    Entity,
    create_gladiator,
    create_player,
)
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
from sanctuary.scenes.arena.tile_map import TileMap
from sanctuary.scenes.arena.simulation import ArenaSimulation
from sanctuary.scenes.arena.state import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    ZOOM_SCALES,
    Arena,
)
from sanctuary.scenes.arena.tiles import (
    BLOOD_FLOOR,
    BLOOD_FLOOR_TEXTURE,
    CHASM,
    CHASM_TEXTURE,
    EMPTY,
    FLOOR,
    FLOOR_TEXTURE,
    RED_GLADIATOR_TEXTURE,
    BLUE_GLADIATOR_TEXTURE,
    PLAYER_TEXTURE,
    WALL,
    WALL_TEXTURE,
    Texture,
    Tile,
)

__all__ = [
    "ARENA_HEIGHT",
    "ARENA_WIDTH",
    "ARENA_PRESETS",
    "Arena",
    "ArenaPreset",
    "ArenaSimulation",
    "BLOOD_FLOOR",
    "BLOOD_FLOOR_TEXTURE",
    "CHASM",
    "CHASM_TEXTURE",
    "EMPTY",
    "Entity",
    "FLOOR",
    "FLOOR_TEXTURE",
    "RED_GLADIATOR_TEXTURE",
    "BLUE_GLADIATOR_TEXTURE",
    "PLAYER_TEXTURE",
    "Texture",
    "Tile",
    "TileMap",
    "WALL",
    "WALL_TEXTURE",
    "ZOOM_SCALES",
    "create_gladiator",
    "create_player",
    "generate_colosseum",
    "generate_concentric_bastions",
    "generate_greek_amphitheater",
    "generate_proving_ground",
    "generate_sierpinski_ruins",
    "generate_tectonic_chasm",
]
