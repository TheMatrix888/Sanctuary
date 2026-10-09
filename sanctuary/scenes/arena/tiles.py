"""
Discrete tile types, physical material flags, and rendering primitives for arena maps.
"""
from enum import IntFlag

from sanctuary.core.primitives import Color


class Tile(IntFlag):
    """Bitmask properties of discrete map cells."""
    EMPTY = 0
    WALKABLE = 1 << 0  # Physical entities can step onto this cell
    OPAQUE = 1 << 1    # Blocks line-of-sight and light propagation
    BLOOD = 1 << 2     # Blood-stained battleground floor
    CHASM = 1 << 3     # Abyss/water hazard: transparent to light, impassable for movement


FLOOR = Tile.WALKABLE
WALL = Tile.OPAQUE
BLOOD_FLOOR = Tile.WALKABLE | Tile.BLOOD
CHASM = Tile.CHASM


def get_tile_render(tile: Tile) -> tuple[str, Color]:
    """Resolves tile bitmask properties into display character and palette color."""
    if tile & Tile.OPAQUE:
        return "#", Color(192, 192, 192)
    if tile & Tile.CHASM:
        return "≈", Color(60, 120, 220)
    if tile & Tile.BLOOD:
        return "·", Color(220, 60, 60)
    return "·", Color(64, 200, 64)
