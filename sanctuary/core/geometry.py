"""
Spatial and geometric primitives for the Sanctuary engine.
Provides fundamental immutable types for 2D terminal coordinates, dimensions, and bounding boxes.
"""
from collections.abc import Callable, Iterator
from dataclasses import dataclass
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


@dataclass(slots=True, frozen=True)
class Rect:
    """
    Immutable 2D axis-aligned bounding box defined by origin (x, y) and dimensions (width, height).
    """
    x: int
    y: int
    width: int
    height: int

    @property
    def left(self) -> int:
        """Left boundary coordinate (inclusive)."""
        return self.x

    @property
    def top(self) -> int:
        """Top boundary coordinate (inclusive)."""
        return self.y

    @property
    def right(self) -> int:
        """Right boundary coordinate (exclusive: x + width)."""
        return self.x + self.width

    @property
    def bottom(self) -> int:
        """Bottom boundary coordinate (exclusive: y + height)."""
        return self.y + self.height

    @property
    def center(self) -> Point:
        """Calculates discrete center coordinate."""
        return Point(self.x + self.width // 2, self.y + self.height // 2)

    def __contains__(self, item: Point | tuple[int, int]) -> bool:
        """Enables pythonic `point in rect` containment checks."""
        point_x = item.x if isinstance(item, Point) else item[0]
        point_y = item.y if isinstance(item, Point) else item[1]
        return self.x <= point_x < self.right and self.y <= point_y < self.bottom

    def __iter__(self) -> Iterator[Point]:
        """Allows direct iteration over all discrete cells inside the bounding box."""
        for cell_y in range(self.y, self.bottom):
            for cell_x in range(self.x, self.right):
                yield Point(cell_x, cell_y)

    def __str__(self) -> str:
        return f"Rect({self.x}, {self.y}, {self.width}x{self.height})"

    @classmethod
    def from_center(cls, center_x: int, center_y: int, width: int, height: int) -> "Rect":
        """Constructs a Rect centered around (center_x, center_y)."""
        return cls(center_x - width // 2, center_y - height // 2, width, height)

    @classmethod
    def from_corners(cls, x1: int, y1: int, x2: int, y2: int) -> "Rect":
        """Constructs an inclusive Rect spanning from (x1, y1) to (x2, y2)."""
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        return cls(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)

def ray8(start: Point, end: Point) -> list[Point]:
    """
    Traces an 8-connected discrete ray using symmetric integer Bresenham stepping.
    Allows single-step diagonal transitions. Includes start and end points.
    """
    sx = 1 if end.x > start.x else (-1 if end.x < start.x else 0)
    sy = 1 if end.y > start.y else (-1 if end.y < start.y else 0)
    dx = abs(end.x - start.x)
    dy = abs(end.y - start.y)
    err = dx - dy
    curr_x, curr_y = start.x, start.y
    points = [Point(curr_x, curr_y)]

    while curr_x != end.x or curr_y != end.y:
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            curr_x += sx
        if e2 < dx:
            err += dx
            curr_y += sy
        points.append(Point(curr_x, curr_y))

    return points


def ray4(start: Point, end: Point) -> list[Point]:
    """
    Traces a 4-connected discrete ray using orthogonal stepping (Manhattan grid traversal).
    Strictly forbids diagonal shortcuts: every step advances exactly 1 cell along X or Y.
    Includes start and end points.
    """
    sx = 1 if end.x > start.x else (-1 if end.x < start.x else 0)
    sy = 1 if end.y > start.y else (-1 if end.y < start.y else 0)
    dx = abs(end.x - start.x)
    dy = abs(end.y - start.y)
    err = dx - dy
    curr_x, curr_y = start.x, start.y
    points = [Point(curr_x, curr_y)]

    while curr_x != end.x or curr_y != end.y:
        err2 = 2 * err
        step_x = err2 > -dy
        step_y = err2 < dx
        if step_x and step_y:
            # Diagonal choice: break into two separate orthogonal steps along the major axis
            if dx >= dy:
                curr_x += sx
                points.append(Point(curr_x, curr_y))
                curr_y += sy
                points.append(Point(curr_x, curr_y))
            else:
                curr_y += sy
                points.append(Point(curr_x, curr_y))
                curr_x += sx
                points.append(Point(curr_x, curr_y))
            err -= dy
            err += dx
        elif step_x:
            err -= dy
            curr_x += sx
            points.append(Point(curr_x, curr_y))
        elif step_y:
            err += dx
            curr_y += sy
            points.append(Point(curr_x, curr_y))

    return points

