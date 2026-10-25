"""
Spatial and geometric primitives for the Sanctuary engine.
Provides fundamental immutable types for 2D terminal coordinates, dimensions, and bounding boxes.
"""
from collections.abc import Callable, Iterator
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


class Rect(NamedTuple):
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


def cast_ray(
    start_x: int,
    start_y: int,
    target_x: int,
    target_y: int,
    is_opaque: Callable[[int, int], bool],
) -> list[Point]:
    """
    Traces a 4-connected discrete ray using supercover integer Bresenham stepping.
    Stops upon encountering an opaque cell, strictly blocking diagonal corner leaks.
    """
    dx = abs(target_x - start_x)
    dy = abs(target_y - start_y)
    sx = 1 if target_x > start_x else -1
    sy = 1 if target_y > start_y else -1
    x, y = start_x, start_y
    err = dx - dy
    visible: list[Point] = [Point(x, y)]

    while x != target_x or y != target_y:
        if is_opaque(x, y):
            break

        e2 = 2 * err
        step_x = e2 > -dy
        step_y = e2 < dx

        # Corner collision check: if stepping in both axes, check both adjacent cells
        if step_x and step_y:
            wall_x = is_opaque(x + sx, y)
            wall_y = is_opaque(x, y + sy)
            if wall_x or wall_y:
                if wall_x:
                    visible.append(Point(x + sx, y))
                if wall_y:
                    visible.append(Point(x, y + sy))
                break

        if step_x:
            err -= dy
            x += sx
        if step_y:
            err += dx
            y += sy

        visible.append(Point(x, y))

    return visible


def field_of_view(
    center_x: int,
    center_y: int,
    view_distance: int,
    is_opaque: Callable[[int, int], bool],
) -> set[Point]:
    """
    Calculates 360-degree circular line-of-sight visibility within Euclidean radius.
    Returns the set of all discrete coordinates visible from (center_x, center_y).
    Includes a wall-face illumination pass to eliminate discrete grazing ray gaps on flat surfaces.
    """
    max_dist_sq = view_distance * view_distance
    visible: set[Point] = set()
    targets: list[Point] = []

    # Bounding perimeter targets
    for target_x in range(center_x - view_distance, center_x + view_distance + 1):
        targets.append(Point(target_x, center_y - view_distance))
        targets.append(Point(target_x, center_y + view_distance))

    for target_y in range(center_y - view_distance + 1, center_y + view_distance):
        targets.append(Point(center_x - view_distance, target_y))
        targets.append(Point(center_x + view_distance, target_y))

    for target in targets:
        for pt in cast_ray(center_x, center_y, target.x, target.y, is_opaque):
            if (pt.x - center_x) ** 2 + (pt.y - center_y) ** 2 <= max_dist_sq:
                visible.add(pt)

    # Wall-face illumination pass:
    # Any opaque wall adjacent to an illuminated transparent tile within circular radius
    # has its face directly lit by ambient line-of-sight, closing discrete grazing ray gaps.
    illuminated_walls: set[Point] = set()
    for point in visible:
        if not is_opaque(point.x, point.y):
            for delta_x, delta_y in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = Point(point.x + delta_x, point.y + delta_y)
                dist_sq = (neighbor.x - center_x) ** 2 + (neighbor.y - center_y) ** 2
                if dist_sq <= max_dist_sq and is_opaque(neighbor.x, neighbor.y):
                    illuminated_walls.add(neighbor)

    visible.update(illuminated_walls)
    return visible
