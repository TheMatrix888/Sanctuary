"""
Discrete 2D tile map model and spatial query methods.
Universal grid representation for arenas, cities, stations, and spaceship decks.
"""
from dataclasses import dataclass

from sanctuary.scenes.arena.tiles import EMPTY, Tile


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
