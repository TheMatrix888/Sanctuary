"""
Discrete physical Tile prototypes for the tactical arena.
Defines material obstruction properties (walkable, opaque) and references visual Texture assets.
"""
from dataclasses import dataclass

from .textures import (
    BLOOD_FLOOR_TEXTURE,
    CHASM_TEXTURE,
    FLOOR_TEXTURE,
    Texture,
    WALL_TEXTURE,
)


@dataclass(slots=True, frozen=True)
class Tile:
    """Discrete grid cell definition with collision, light occlusion, and visual asset binding."""
    walkable: bool
    opaque: bool
    texture: Texture


# =============================================================================
# STANDARD PHYSICAL TILE PROTOTYPES
# =============================================================================

WALL = Tile(walkable=False, opaque=True, texture=WALL_TEXTURE)
FLOOR = Tile(walkable=True, opaque=False, texture=FLOOR_TEXTURE)
BLOOD_FLOOR = Tile(walkable=True, opaque=False, texture=BLOOD_FLOOR_TEXTURE)
CHASM = Tile(walkable=False, opaque=False, texture=CHASM_TEXTURE)
EMPTY = Tile(walkable=False, opaque=True, texture=FLOOR_TEXTURE)

"""
◑  ◐
//\\\\

▆▂▂▆ 
▊ε ▊

▆▂▂▆
▊▽ ▊

▆▂▂▆
╳◠ ╳

◭▽ ◮
┑__┎

◭▽ ◮
┑◟◞┎
"""
