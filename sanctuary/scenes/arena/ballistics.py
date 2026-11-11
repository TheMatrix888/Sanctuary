"""
Ballistic raycasting and screen-space vector beam rasterization.
Provides sub-pixel continuous bullet trajectories decoupled from discrete tile textures.
"""
from dataclasses import dataclass
from typing import Callable

from sanctuary.core.geometry import Point, cast_ray
from sanctuary.core.primitives import Cell, Color
from sanctuary.core.screen import Screen

BEAM_COLOR = Color(255, 200, 50)
HIT_COLOR = Color(255, 100, 40)


@dataclass(slots=True, frozen=True)
class ShotRay:
    """
    Geometric representation of a ballistic projectile trajectory on the tilemap grid.
    Decoupled from screen resolution, allowing seamless dynamic scale switching.
    """
    start: Point
    target: Point
    hit: Point
    path: tuple[Point, ...] = ()
    is_impact: bool = True


def clamp_to_radius(center_x: int, center_y: int, target_x: int, target_y: int, radius: int) -> tuple[int, int]:
    """
    Clamps (target_x, target_y) to the discrete Euclidean circle of radius `radius` centered at (center_x, center_y).
    Guarantees the clamped point satisfies (x - cx)^2 + (y - cy)^2 <= radius^2.
    """
    dx = target_x - center_x
    dy = target_y - center_y
    if dx * dx + dy * dy <= radius * radius:
        return target_x, target_y

    distance = (dx * dx + dy * dy) ** 0.5
    factor = radius / distance
    clamped_x = center_x + round(dx * factor)
    clamped_y = center_y + round(dy * factor)

    # Step back along the major axis until strictly within Euclidean boundary
    while (clamped_x - center_x) ** 2 + (clamped_y - center_y) ** 2 > radius * radius:
        step_x = 1 if clamped_x > center_x else (-1 if clamped_x < center_x else 0)
        step_y = 1 if clamped_y > center_y else (-1 if clamped_y < center_y else 0)
        if abs(clamped_x - center_x) >= abs(clamped_y - center_y):
            clamped_x -= step_x
        else:
            clamped_y -= step_y

    return clamped_x, clamped_y


def trace_shot_ray(
    shooter_x: int,
    shooter_y: int,
    target_x: int,
    target_y: int,
    is_opaque: Callable[[int, int], bool],
    view_distance: int | None = None,
) -> ShotRay:
    """
    Traces a discrete ballistic ray on the tilemap grid.
    Stops upon encountering an opaque obstacle, landing in the floor cell immediately before the wall (prev_point).
    Guarantees zero diagonal wall corner leaks and clamps to circular Euclidean FOV boundary.
    """
    start = Point(shooter_x, shooter_y)
    if view_distance is not None:
        target_x, target_y = clamp_to_radius(shooter_x, shooter_y, target_x, target_y, view_distance)
    target = Point(target_x, target_y)

    dx = abs(target_x - shooter_x)
    dy = abs(target_y - shooter_y)
    sx = 1 if target_x > shooter_x else -1
    sy = 1 if target_y > shooter_y else -1
    err = dx - dy
    curr_x, curr_y = shooter_x, shooter_y
    prev_x, prev_y = shooter_x, shooter_y
    path: list[Point] = [start]

    while True:
        if curr_x == target_x and curr_y == target_y:
            if is_opaque(curr_x, curr_y):
                return ShotRay(
                    start=start,
                    target=target,
                    hit=Point(prev_x, prev_y),
                    path=tuple(path),
                    is_impact=True,
                )
            return ShotRay(
                start=start,
                target=target,
                hit=target,
                path=tuple(path),
                is_impact=False,
            )

        e2 = 2 * err
        step_x = e2 > -dy
        step_y = e2 < dx

        # Corner collision check: if stepping in both axes, check both adjacent cells
        if step_x and step_y:
            wall_x = is_opaque(curr_x + sx, curr_y)
            wall_y = is_opaque(curr_x, curr_y + sy)
            if wall_x or wall_y:
                return ShotRay(
                    start=start,
                    target=target,
                    hit=Point(curr_x, curr_y),
                    path=tuple(path),
                    is_impact=True,
                )

        if step_x:
            err -= dy
            curr_x += sx
        if step_y:
            err += dx
            curr_y += sy

        if is_opaque(curr_x, curr_y):
            return ShotRay(
                start=start,
                target=target,
                hit=Point(prev_x, prev_y),
                path=tuple(path),
                is_impact=True,
            )

        path.append(Point(curr_x, curr_y))
        prev_x, prev_y = curr_x, curr_y


def draw_shot_ray(
    screen: Screen,
    shot: ShotRay,
    origin_x: int,
    origin_y: int,
    scale: tuple[int, int] = (1, 1),
) -> None:
    """
    Renders a continuous, gapless ballistic beam into the screen back buffer.
    Guarantees strict 8-connected continuity with zero dropped or broken segments.
    """
    scale_w, scale_h = scale

    shooter_min_x = origin_x + shot.start.x * scale_w
    shooter_max_x = shooter_min_x + scale_w
    shooter_min_y = origin_y + shot.start.y * scale_h
    shooter_max_y = shooter_min_y + scale_h

    # Target hit coordinate: top-left corner (col 0, row 0) of the hit tile (floor dot '.' indicator)
    screen_start_x = shooter_min_x
    screen_start_y = shooter_min_y
    screen_hit_x = origin_x + shot.hit.x * scale_w
    screen_hit_y = origin_y + shot.hit.y * scale_h

    # Point-blank impact spark
    if screen_start_x == screen_hit_x and screen_start_y == screen_hit_y:
        if 0 <= screen_hit_y < screen.size.rows and 0 <= screen_hit_x < screen.size.columns:
            screen.back_buffer.set_cell(screen_hit_x, screen_hit_y, Cell(char="*", fg_color=HIT_COLOR))
        return

    dx = screen_hit_x - screen_start_x
    dy = screen_hit_y - screen_start_y
    abs_dx = abs(dx)
    abs_dy = abs(dy)
    step_dir_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
    step_dir_y = 1 if dy > 0 else (-1 if dy < 0 else 0)

    is_pure_horizontal = (dy == 0)
    is_pure_vertical = (dx == 0)
    diag_char = "\\" if (step_dir_x * step_dir_y > 0) else "/"

    err = abs_dx - abs_dy
    curr_x, curr_y = screen_start_x, screen_start_y
    screen_points: list[tuple[int, int]] = []

    while True:
        screen_points.append((curr_x, curr_y))
        if curr_x == screen_hit_x and curr_y == screen_hit_y:
            break
        e2 = 2 * err
        step_x = e2 > -abs_dy
        step_y = e2 < abs_dx
        if step_x:
            err -= abs_dy
            curr_x += step_dir_x
        if step_y:
            err += abs_dx
            curr_y += step_dir_y

    # Rasterize along screen trajectory, skipping shooter origin tile footprint
    total_points = len(screen_points)
    for index in range(1, total_points):
        point_x, point_y = screen_points[index]
        if not (0 <= point_y < screen.size.rows and 0 <= point_x < screen.size.columns):
            continue

        if shooter_min_x <= point_x < shooter_max_x and shooter_min_y <= point_y < shooter_max_y:
            continue

        # Impact terminal spark (always at top-left of target tile)
        if index == total_points - 1:
            screen.back_buffer.set_cell(point_x, point_y, Cell(char="*", fg_color=HIT_COLOR))
            continue

        prev_x, prev_y = screen_points[index - 1]
        delta_x = point_x - prev_x
        delta_y = point_y - prev_y

        if is_pure_horizontal:
            char = "-"
        elif is_pure_vertical:
            char = "|"
        else:
            if delta_x != 0 and delta_y == 0:
                char = "-"
            else:
                char = diag_char

        # Vertical invariant: no diagonal slash directly above or below another diagonal slash
        above_char = screen.back_buffer.cells[point_y - 1][point_x].char if point_y > 0 else ""
        below_char = screen.back_buffer.cells[point_y + 1][point_x].char if point_y + 1 < screen.size.rows else ""

        if char in ("\\", "/"):
            if above_char == char or below_char == char:
                char = "|"

        # Horizontal invariant: strictly prevent '//' and '\\\\' horizontally adjacent
        left_char = screen.back_buffer.cells[point_y][point_x - 1].char if point_y > 0 else ""
        right_char = screen.back_buffer.cells[point_y][point_x + 1].char if point_x + 1 < screen.size.columns else ""

        if char in ("\\", "/"):
            if left_char == char or right_char == char:
                char = "-"

        screen.back_buffer.set_cell(point_x, point_y, Cell(char=char, fg_color=BEAM_COLOR))
