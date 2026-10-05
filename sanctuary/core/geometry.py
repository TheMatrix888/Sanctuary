"""
Spatial and geometric primitives for the Sanctuary engine.
Provides fundamental immutable types for 2D terminal coordinates, dimensions, and bounding boxes.
"""
from typing import NamedTuple


class Point(NamedTuple):
    """
    Immutable 2D discrete coordinate in character cell space.
    """
    x: int
    y: int

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"


class Size(NamedTuple):
    """
    Immutable 2D dimensions for viewports, buffers, surfaces, and UI elements.
    Provides dual-vocabulary access:
      - Graphics convention: width, height
      - Terminal convention: columns, rows
    """
    width: int
    height: int

    @property
    def columns(self) -> int:
        """Alias for width in character cells."""
        return self.width

    @property
    def rows(self) -> int:
        """Alias for height in character cells."""
        return self.height

    @property
    def total_cells(self) -> int:
        """Calculates total area / cell capacity (width * height)."""
        return self.width * self.height

    def __str__(self) -> str:
        return f"{self.width}x{self.height} ({self.total_cells:,} cells)"
