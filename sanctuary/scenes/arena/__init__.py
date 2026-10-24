"""
Arena package: tactical procedural combat sandbox, discrete raytracing, and map presets.
"""
from .config import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    GENOME_SIZE,
    ZOOM_SCALES,
)
from .entities import (
    Entity,
    create_player,
)
from .generators import (
    ARENA_PRESETS,
    generate_colosseum,
    generate_concentric_bastions,
    generate_greek_amphitheater,
    generate_proving_ground,
    generate_sierpinski_ruins,
    generate_tectonic_chasm,
)
from .gladiator import (
    Gladiator,
    create_gladiator,
)
from .simulation import ArenaSimulation
from .worker import (
    Mode,
    PlaybackSettings,
    WorldConfig,
    SimulationWorker,
    Snapshot,
    run_simulation_worker,
)
from .state import Arena
from .textures import (
    BLOOD_FLOOR_TEXTURE,
    BLUE_GLADIATOR_TEXTURE,
    CHASM_TEXTURE,
    DEAD_BLUE_GLADIATOR_TEXTURE,
    DEAD_RED_GLADIATOR_TEXTURE,
    FLOOR_TEXTURE,
    PLAYER_TEXTURE,
    RED_GLADIATOR_TEXTURE,
    Texture,
    WALL_TEXTURE,
)
from .tile_map import TileMap
from .tiles import (
    BLOOD_FLOOR,
    CHASM,
    EMPTY,
    FLOOR,
    Tile,
    WALL,
)

__all__ = [
    "ARENA_HEIGHT",
    "ARENA_WIDTH",
    "ARENA_PRESETS",
    "Arena",
    "ArenaSimulation",
    "BLOOD_FLOOR",
    "BLOOD_FLOOR_TEXTURE",
    "BLUE_GLADIATOR_TEXTURE",
    "CHASM",
    "CHASM_TEXTURE",
    "DEAD_BLUE_GLADIATOR_TEXTURE",
    "DEAD_RED_GLADIATOR_TEXTURE",
    "EMPTY",
    "Entity",
    "FLOOR",
    "FLOOR_TEXTURE",
    "GENOME_SIZE",
    "Gladiator",
    "Mode",
    "PlaybackSettings",
    "PLAYER_TEXTURE",
    "RED_GLADIATOR_TEXTURE",
    "WorldConfig",
    "SimulationWorker",
    "Snapshot",
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
    "run_simulation_worker",
]
