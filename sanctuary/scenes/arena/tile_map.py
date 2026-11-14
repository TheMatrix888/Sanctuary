"""
Discrete 2D tile map model, spatial queries, and unified rendering.
Universal grid representation for arenas, cities, stations, and spaceship decks.
"""
from collections.abc import Collection, Mapping
from dataclasses import dataclass

from sanctuary.core.geometry import Point
from sanctuary.core.screen import Screen

from .tiles import EMPTY, Tile


@dataclass(slots=True)
class TileMap:
    """Discrete tile grid representing spatial layout and physical material properties."""
    width: int
    height: int
    tiles: list[list[Tile]]

    def is_opaque(self, x: int, y: int) -> bool:
        """Determines if a cell blocks vision. Out-of-bounds cells are opaque."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x].opaque
        return True

    def is_walkable(self, x: int, y: int) -> bool:
        """Determines if an entity can enter the cell. Out-of-bounds is non-walkable."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x].walkable
        return False

    def get_tile(self, x: int, y: int) -> Tile:
        """Retrieves tile prototype at the specified discrete coordinate."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return EMPTY

    def set_tile(self, x: int, y: int, tile: Tile) -> None:
        """Updates tile prototype at the specified discrete coordinate."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = tile

    def draw(
        self,
        screen: Screen,
        origin_x: int,
        origin_y: int,
        scale: tuple[int, int] = (1, 1),
        visible_cells: dict[Point, int] | None = None,
        show_vertices: bool = False,
    ) -> None:
        """
        Renders the tilemap onto the screen at the given origin with footprint scaling.
        If visible_cells is provided, renders only those illuminated coordinates (raytracing).
        """
        scale_w, scale_h = scale
        if visible_cells is not None:
            for point in visible_cells:
                tile = self.get_tile(point.x, point.y)
                if tile != EMPTY:
                    screen_x = origin_x + point.x * scale_w
                    screen_y = origin_y + point.y * scale_h
                    surface = tile.texture.get_surface(scale)
                    screen.draw_surface(screen_x, screen_y, surface)
                    if show_vertices and self.is_walkable(point.x, point.y):
                        screen.draw_text(screen_x, screen_y, str(visible_cells[point]))
        else:
            for y in range(self.height):
                for x in range(self.width):
                    tile = self.get_tile(x, y)
                    if tile != EMPTY:
                        screen_x = origin_x + x * scale_w
                        screen_y = origin_y + y * scale_h
                        surface = tile.texture.get_surface(scale)
                        screen.draw_surface(screen_x, screen_y, surface)
