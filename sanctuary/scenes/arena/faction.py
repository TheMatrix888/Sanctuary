"""
Domain models and registry for arena combatant factions inspired by Age of Empires 1.
Encapsulates team identities, canonical colors, and pre-rendered gladiator textures.
"""
from dataclasses import dataclass

from sanctuary.core.primitives import Color

from .textures import DEAD_GLADIATOR_TEXTURE, GLADIATOR_TEXTURE, Texture


@dataclass(slots=True, frozen=True)
class Faction:
    """
    Domain representation of an arena combatant faction.
    Encapsulates identity (id, name), visual styling (color), and pre-rendered textures.
    """
    id: int
    name: str
    color: Color
    alive_texture: Texture
    dead_texture: Texture

    @classmethod
    def create(cls, id: int, name: str, color: Color) -> "Faction":
        """Factory creating a faction with colored alive and dead gladiator textures."""
        return cls(
            id=id,
            name=name,
            color=color,
            alive_texture=GLADIATOR_TEXTURE.with_color(fg_color=color),
            dead_texture=DEAD_GLADIATOR_TEXTURE.with_color(fg_color=color),
        )


# =============================================================================
# AGE OF EMPIRES 1 CANONICAL FACTIONS (1..8)
# =============================================================================

BLUE = Faction.create(1, "Blue", Color(0, 0, 255))
RED = Faction.create(2, "Red", Color(255, 0, 0))
YELLOW = Faction.create(3, "Yellow", Color(255, 255, 0))
BROWN = Faction.create(4, "Brown", Color(116, 66, 49))
ORANGE = Faction.create(5, "Orange", Color(227, 115, 6))
LIME = Faction.create(6, "Lime", Color(0, 255, 0))
GRAY = Faction.create(7, "Gray", Color(192, 192, 192))
TEAL = Faction.create(8, "Teal", Color(0, 128, 128))

ALL_FACTIONS: tuple[Faction, ...] = (
    BLUE,
    RED,
    YELLOW,
    BROWN,
    ORANGE,
    LIME,
    GRAY,
    TEAL,
)

FACTIONS_BY_ID: dict[int, Faction] = {faction.id: faction for faction in ALL_FACTIONS}
FACTIONS_BY_NAME: dict[str, Faction] = {faction.name.lower(): faction for faction in ALL_FACTIONS}
FACTIONS_BY_NAME["green"] = LIME
