"""
Entity and actor models for the tactical arena.
Provides unified Entity dataclass with embedded multi-resolution Texture assets.
"""
from dataclasses import dataclass

from sanctuary.core.primitives import Color, Surface
from sanctuary.scenes.arena.tiles import (
    Texture,
    RED_GLADIATOR_TEXTURE, BLUE_GLADIATOR_TEXTURE,
    PLAYER_TEXTURE,
)


@dataclass(slots=True)
class Entity:
    """
    Dynamic grid entity model representing actors (player, gladiators) on the arena grid.
    Owns a Texture asset providing multi-resolution Surface representations (1x1, 2x1, 4x2).
    """
    x: int
    y: int
    texture: Texture
    view_distance: int = 10
    dx: int = 0
    dy: int = 0
    hp: int = 100
    max_hp: int = 100
    is_player: bool = False

    @property
    def glyph(self) -> str:
        """Returns 1x1 character glyph from the underlying texture."""
        return self.texture.glyph_1x1.cells[0][0].char

    @property
    def fg_color(self) -> Color:
        """Returns primary foreground color from the underlying texture."""
        return self.texture.glyph_1x1.cells[0][0].fg_color


def create_player(x: int, y: int, view_distance: int = 10) -> Entity:
    """Factory creating a player entity with magenta styling and circular FOV."""
    return Entity(
        x=x,
        y=y,
        texture=PLAYER_TEXTURE,
        view_distance=view_distance,
        is_player=True,
    )


def create_gladiator(
        x: int,
        y: int,
        team: str = "red",
        view_distance: int = 8,
) -> Entity:
    """Factory creating an AI gladiator entity."""
    if team == "red":
        texture = RED_GLADIATOR_TEXTURE
    else:
        texture = BLUE_GLADIATOR_TEXTURE

    return Entity(
        x=x,
        y=y,
        texture=texture,
        view_distance=view_distance,
        is_player=False,
    )
