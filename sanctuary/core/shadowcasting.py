"""
Discrete Roguelike Shadowcasting algorithm for Field of View (FOV).
Calculates line-of-sight visibility and visible corner vertex counts (1-4)
across 8 symmetrical octants using rational slope intervals.
"""
from typing import Callable

from .geometry import Point

# Octant transformation matrices (xx, xy, yx, yy)
# Global coordinates:
#   global_x = center.x + x * xx + y * xy
#   global_y = center.y + x * yx + y * yy
OCTANTS: tuple[tuple[int, int, int, int], ...] = (
    (0, 1, 1, 0),    # East-North-East
    (1, 0, 0, 1),    # North-East
    (-1, 0, 0, 1),   # North-West
    (0, -1, 1, 0),   # West-North-West
    (0, -1, -1, 0),  # West-South-West
    (-1, 0, 0, -1),  # South-West
    (1, 0, 0, -1),   # South-East
    (0, 1, -1, 0),   # East-South-East
)


def octant_shadowcast(
    center: Point,
    view_distance: int,
    is_opaque: Callable[[int, int], bool],
    octant: tuple[int, int, int, int],
) -> dict[Point, int]:
    """
    Computes visibility within a single 45-degree octant.
    Returns a mapping of visible Points to their count of unblocked vertices (1-4).
    """
    visible: dict[Point, int] = {}
    xx, xy, yx, yy = octant
    blocked_intervals: list[tuple[float, float]] = []

    for x in range(1, view_distance + 1):
        # Early exit: entire angular span [0.0, 1.0] is submerged in shadow
        if blocked_intervals and any(lower <= 0.0 and upper >= 1.0 for lower, upper in blocked_intervals):
            break

        for y in range(x + 1):
            global_x = center.x + x * xx + y * xy
            global_y = center.y + x * yx + y * yy

            vertices_slope = (
                (y - 0.5) / (x - 0.5),  # upper-left
                (y + 0.5) / (x - 0.5),  # upper-right
                (y - 0.5) / (x + 0.5),  # lower-left
                (y + 0.5) / (x + 0.5),  # lower-right
            )
            min_slope = min(vertices_slope)
            max_slope = max(vertices_slope)

            # A cell is blocked only if its full angular extent is covered by a single solid shadow
            is_blocked = False
            for lower, upper in blocked_intervals:
                if lower <= min_slope and max_slope <= upper:
                    is_blocked = True
                    break

            if is_blocked:
                continue

            # Count visible vertices not enclosed in any shadow interval
            seen_vertices = sum(
                1 for slope in vertices_slope
                if not any(lower <= slope <= upper for lower, upper in blocked_intervals)
            )
            # If light illuminates the cell face through a gap, at least 1 vertex exposure is guaranteed
            seen_vertices = max(1, seen_vertices)

            pt = Point(global_x, global_y)
            visible[pt] = max(visible.get(pt, 0), seen_vertices)

            if is_opaque(global_x, global_y):
                lower = min_slope
                upper = max_slope

                overlapping: list[tuple[float, float]] = []
                non_overlapping: list[tuple[float, float]] = []
                for interval in blocked_intervals:
                    if interval[0] <= upper and lower <= interval[1]:
                        overlapping.append(interval)
                    else:
                        non_overlapping.append(interval)

                for interval in overlapping:
                    lower = min(lower, interval[0])
                    upper = max(upper, interval[1])
                non_overlapping.append((lower, upper))
                blocked_intervals = non_overlapping

    return visible


def field_of_view(
    center: Point,
    view_distance: int,
    is_opaque: Callable[[int, int], bool],
) -> dict[Point, int]:
    """
    Calculates complete 360-degree field of view using 8-octant discrete shadowcasting.
    Returns a mapping of Point -> visible vertices count (1-4).
    Center origin always has all 4 vertices visible.
    """
    visible: dict[Point, int] = {center: 4}

    for octant in OCTANTS:
        octant_visible = octant_shadowcast(center, view_distance, is_opaque, octant)
        for pt, count in octant_visible.items():
            visible[pt] = max(visible.get(pt, 0), count)

    return visible
