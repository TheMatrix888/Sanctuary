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
    cycle_next_map,
    generate_colosseum,
    generate_concentric_bastions,
    generate_greek_amphitheater,
    generate_proving_ground,
    generate_sierpinski_ruins,
    generate_tectonic_chasm,
)
from .faction import (
    ALL_FACTIONS,
    BLUE,
    BROWN,
    FACTIONS_BY_ID,
    FACTIONS_BY_NAME,
    Faction,
    GRAY,
    LIME,
    ORANGE,
    RED,
    TEAL,
    YELLOW,
)
from .gladiator import (
    Gladiator,
    create_gladiator,
)
from .setup import ArenaSetupState
from .running import ArenaRunningState
from .models import (
    BlinkIndicator,
    GenerationRecord,
    GpsTracker,
    Mode,
    PlaybackSettings,
    SimulationSave,
    Snapshot,
    WorldConfig,
)
from .worker import (
    SimulationWorker,
    run_simulation_worker,
)
from .ballistics import (
    BEAM_COLOR,
    HIT_COLOR,
    ShotRay,
    draw_shot_ray,
    trace_shot_ray,
)
from .arena import (
    Arena,
)
from .textures import (
    BLOOD_FLOOR_TEXTURE,
    CHASM_TEXTURE,
    DEAD_GLADIATOR_TEXTURE,
    FLOOR_TEXTURE,
    GLADIATOR_TEXTURE,
    PLAYER_TEXTURE,
    RETICLE_AMBER_TEXTURE,
    RETICLE_RED_TEXTURE,
    SelectionTexture,
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
    "ALL_FACTIONS",
    "ARENA_HEIGHT",
    "ARENA_WIDTH",
    "ARENA_PRESETS",
    "Arena",
    "ArenaSetupState",
    "ArenaRunningState",
    "BEAM_COLOR",
    "BLOOD_FLOOR",
    "BLOOD_FLOOR_TEXTURE",
    "BLUE",
    "BROWN",
    "BlinkIndicator",
    "CHASM",
    "CHASM_TEXTURE",
    "DEAD_GLADIATOR_TEXTURE",
    "EMPTY",
    "Entity",
    "FACTIONS_BY_ID",
    "FACTIONS_BY_NAME",
    "Faction",
    "FLOOR",
    "FLOOR_TEXTURE",
    "GENOME_SIZE",
    "GenerationRecord",
    "GLADIATOR_TEXTURE",
    "Gladiator",
    "GpsTracker",
    "GRAY",
    "HIT_COLOR",
    "LIME",
    "Mode",
    "ORANGE",
    "PlaybackSettings",
    "PLAYER_TEXTURE",
    "RED",
    "RETICLE_AMBER_TEXTURE",
    "RETICLE_RED_TEXTURE",
    "SelectionTexture",
    "ShotRay",
    "WorldConfig",
    "SimulationWorker",
    "SimulationSave",
    "Snapshot",
    "TEAL",
    "Texture",
    "Tile",
    "TileMap",
    "WALL",
    "WALL_TEXTURE",
    "YELLOW",
    "ZOOM_SCALES",
    "create_gladiator",
    "create_player",
    "cycle_next_map",
    "draw_shot_ray",
    "generate_colosseum",
    "generate_concentric_bastions",
    "generate_greek_amphitheater",
    "generate_proving_ground",
    "generate_sierpinski_ruins",
    "generate_tectonic_chasm",
    "run_simulation_worker",
    "trace_shot_ray",
]
