"""
Entity and actor models for the tactical arena.
Provides unified Entity dataclass with embedded multi-resolution Texture assets and rendering.
"""
from dataclasses import dataclass

from sanctuary.core.screen import Screen

from .textures import (
    BLUE_GLADIATOR_TEXTURE,
    PLAYER_TEXTURE,
    RED_GLADIATOR_TEXTURE,
    Texture,
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

    def draw(
        self,
        screen: Screen,
        origin_x: int,
        origin_y: int,
        scale: tuple[int, int] = (1, 1),
        transparent_space: bool = False,
    ) -> None:
        """Draws the entity to the target screen at discrete origin offset with LOD scaling."""
        scale_w, scale_h = scale
        screen_x = origin_x + self.x * scale_w
        screen_y = origin_y + self.y * scale_h
        surface = self.texture.get_surface(scale)
        screen.draw_surface(screen_x, screen_y, surface, transparent_space=transparent_space)


def create_player(x: int, y: int, view_distance: int = 10) -> Entity:
    """Factory creating a player entity with magenta styling and circular FOV."""
    return Entity(
        x=x,
        y=y,
        texture=PLAYER_TEXTURE,
        view_distance=view_distance,
    )


def create_gladiator(
    x: int,
    y: int,
    texture: Texture,
    view_distance: int = 8,
) -> Entity:
    """Factory creating an AI gladiator entity."""
    return Entity(
        x=x,
        y=y,
        texture=texture,
        view_distance=view_distance,
    )
