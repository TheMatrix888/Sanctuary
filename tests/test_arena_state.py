"""
Unit tests for interactive Arena state, SelectionTexture framing, and map cycling.
"""
from sanctuary.core.geometry import Point, Size
from sanctuary.core.input_handler import VirtualInputHandler
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.terminal import VirtualTerminal
from sanctuary.scenes.arena import (
    ARENA_HEIGHT,
    ARENA_PRESETS,
    ARENA_WIDTH,
    Arena,
    RETICLE_AMBER_TEXTURE,
    RETICLE_RED_TEXTURE,
    SelectionTexture,
    ShotRay,
    TileMap,
    FLOOR,
    WALL,
    cycle_next_map,
    draw_shot_ray,
    trace_shot_ray,
)


def test_selection_texture_framing_dimensions() -> None:
    # Verify framing dimensions expand cell width by +2 columns:
    # 1x1 -> 3x1
    assert RETICLE_AMBER_TEXTURE.frame_1x1.size == Size(3, 1)
    # 2x1 -> 4x1
    assert RETICLE_AMBER_TEXTURE.frame_2x1.size == Size(4, 1)
    # 2x2 -> 4x2
    assert RETICLE_AMBER_TEXTURE.frame_2x2.size == Size(4, 2)
    # 4x2 -> 6x2
    assert RETICLE_AMBER_TEXTURE.frame_4x2.size == Size(6, 2)

    # Colors
    assert RETICLE_AMBER_TEXTURE.frame_1x1.cells[0][0].fg_color == Color(255, 190, 40)
    assert RETICLE_RED_TEXTURE.frame_1x1.cells[0][0].fg_color == Color(255, 60, 60)


def test_selection_texture_drawing_offset() -> None:
    terminal = VirtualTerminal(columns=40, rows=20)
    screen = Screen(terminal)

    # Drawing at origin (10, 5) for tile (2, 3) at scale (2, 1):
    # screen_x = 10 + 2 * 2 - 1 = 13
    # screen_y = 5 + 3 * 1 = 8
    RETICLE_AMBER_TEXTURE.draw(screen, origin_x=10, origin_y=5, tile_x=2, tile_y=3, scale=(2, 1))

    # Cells at (13, 8) and (16, 8) must have '[' and ']'
    assert screen.back_buffer.cells[8][13].char == "["
    assert screen.back_buffer.cells[8][16].char == "]"

    # Drawing at scale (2, 2) uses box-drawing corners ┌ ┐ and └ ┘
    RETICLE_AMBER_TEXTURE.draw(screen, origin_x=10, origin_y=5, tile_x=2, tile_y=3, scale=(2, 2))
    # screen_x = 13, screen_y = 5 + 3 * 2 = 11
    assert screen.back_buffer.cells[11][13].char == "┌"
    assert screen.back_buffer.cells[11][16].char == "┐"
    assert screen.back_buffer.cells[12][13].char == "└"
    assert screen.back_buffer.cells[12][16].char == "┘"


def test_cycle_next_map() -> None:
    map_keys = list(ARENA_PRESETS.keys())
    assert len(map_keys) >= 2

    # Sequential cycling
    first = map_keys[0]
    second = map_keys[1]
    assert cycle_next_map(first) == second

    # Wrap-around
    last = map_keys[-1]
    assert cycle_next_map(last) == first

    # Unknown key defaults to first
    assert cycle_next_map("NonExistentMap") == first


def test_arena_crosshair_bounds_and_fov_color() -> None:
    arena = Arena()
    assert arena.map == "Colosseum Arena"
    assert isinstance(arena.crosshair, Point)

    # Crosshair clamped to arena boundaries
    arena.shooting = True
    arena.dx = -100
    arena.dy = -100
    arena.update(0.016, Size(100, 40))
    # Should not move out of bounds
    assert 0 <= arena.crosshair.x < ARENA_WIDTH
    assert 0 <= arena.crosshair.y < ARENA_HEIGHT

    arena.dx = 1000
    arena.dy = 1000
    arena.update(0.016, Size(100, 40))
    # Out of bounds attempt rejected
    assert 0 <= arena.crosshair.x < ARENA_WIDTH
    assert 0 <= arena.crosshair.y < ARENA_HEIGHT

    # Check FOV membership: player cell is always in FOV
    assert Point(arena.player.x, arena.player.y) in arena.visible_cells
    # Distant corner cell is NOT in initial player FOV (view_distance = 10)
    assert Point(0, 0) not in arena.visible_cells


def test_trace_shot_ray_physics() -> None:
    width, height = 20, 20
    tilemap = TileMap(width, height, [[FLOOR for _ in range(width)] for _ in range(height)])

    # Horizontal ray: (5, 5) -> (8, 5)
    ray_h = trace_shot_ray(5, 5, 8, 5, tilemap.is_opaque)
    assert ray_h.start == Point(5, 5)
    assert ray_h.target == Point(8, 5)
    assert ray_h.hit == Point(8, 5)

    # Vertical ray: (5, 5) -> (5, 2)
    ray_v = trace_shot_ray(5, 5, 5, 2, tilemap.is_opaque)
    assert ray_v.start == Point(5, 5)
    assert ray_v.target == Point(5, 2)
    assert ray_v.hit == Point(5, 2)

    # Diagonal ray: (5, 5) -> (7, 7)
    ray_diag = trace_shot_ray(5, 5, 7, 7, tilemap.is_opaque)
    assert ray_diag.start == Point(5, 5)
    assert ray_diag.target == Point(7, 7)
    assert ray_diag.hit == Point(7, 7)

    # Obstacle collision terminates ray in front of wall (prev_point)
    tilemap.set_tile(7, 5, WALL)
    ray_wall = trace_shot_ray(5, 5, 9, 5, tilemap.is_opaque)
    assert ray_wall.start == Point(5, 5)
    assert ray_wall.target == Point(9, 5)
    assert ray_wall.hit == Point(6, 5)
    assert ray_wall.is_impact is True

    # Circular FOV Euclidean clamping
    ray_clamped_h = trace_shot_ray(5, 5, 20, 5, tilemap.is_opaque, view_distance=5)
    assert ray_clamped_h.target == Point(10, 5)

    ray_clamped_diag = trace_shot_ray(5, 5, 20, 20, tilemap.is_opaque, view_distance=5)
    dist_sq = (ray_clamped_diag.target.x - 5) ** 2 + (ray_clamped_diag.target.y - 5) ** 2
    assert dist_sq <= 25


def test_draw_shot_ray_pipe_never_enters_wall() -> None:
    """
    Verifies that continuous ballistic beams across multi-resolution footprints (including 4x2)
    never draw beam characters ('-', '|', '\\', '/') inside opaque wall cells.
    """
    from sanctuary.scenes.arena.ballistics import BEAM_COLOR

    terminal = VirtualTerminal(columns=140, rows=40)
    screen = Screen(terminal)

    arena = Arena(map_name="Colosseum Arena")
    arena.shooting = True

    scales = [(1, 1), (2, 1), (2, 2), (4, 2)]
    for scale_idx in range(len(scales)):
        arena.scale_index = scale_idx
        scale_w, scale_h = scales[scale_idx]

        for target_offset in [
            (10, 5), (5, 10), (-8, 6), (7, -7), (0, -10), (12, 0),
            (-7, 1), (7, 1), (-6, 4), (5, 4), (-5, -3),
        ]:
            arena.crosshair = Point(arena.player.x + target_offset[0], arena.player.y + target_offset[1])
            arena.fire()

            screen.clear()
            arena.draw(screen)

            center_col = terminal.columns // 2
            center_row = terminal.rows // 2
            origin_x = center_col - arena.player.x * scale_w
            origin_y = center_row - arena.player.y * scale_h

            for r in range(terminal.rows):
                for c in range(terminal.columns):
                    cell = screen.back_buffer.cells[r][c]
                    if cell.fg_color == BEAM_COLOR and cell.char in ("-", "|", "\\", "/"):
                        tile_x = (c - origin_x) // scale_w
                        tile_y = (r - origin_y) // scale_h
                        if 0 <= tile_x < arena.tilemap.width and 0 <= tile_y < arena.tilemap.height:
                            assert not arena.tilemap.is_opaque(tile_x, tile_y), (
                                f"Beam char '{cell.char}' at screen ({c}, {r}) drawn inside wall tile ({tile_x}, {tile_y}) for scale {arena.tile_scale}"
                            )


def test_draw_shot_ray_corner_wall_diagonal() -> None:
    """
    Verifies that when shooting diagonally toward a corner wall from (1, 2) to (0, 0),
    the intermediate cell renders as a diagonal stroke '\\' rather than a vertical pipe '|'.
    """
    terminal = VirtualTerminal(columns=10, rows=10)
    screen = Screen(terminal)

    shot = ShotRay(start=Point(1, 2), target=Point(0, 0), hit=Point(0, 0), is_impact=True)
    draw_shot_ray(screen, shot, origin_x=0, origin_y=0, scale=(1, 1))

    # (0, 0) is hit spark '*'
    # (1, 1) is diagonal beam '\\'
    # (1, 2) is shooter origin (cleared / unpainted)
    assert screen.back_buffer.cells[0][0].char == "*"
    assert screen.back_buffer.cells[1][1].char == "\\"
    assert screen.back_buffer.cells[2][1].char == " "


def test_arena_360_degree_shot_forbidden_patterns_invariant() -> None:
    """
    Tests 360-degree shooting on an empty map across all multi-resolution scales (1x1, 2x1, 2x2, 4x2).
    Enforces the strict visual invariant: the rendered virtual terminal buffer MUST NEVER contain
    forbidden double patterns: '//', '\\\\', or '||'.
    """
    import math

    arena = Arena(map_name="Empty Proving Ground")
    arena.raytracing_enabled = False
    arena.shooting = True
    terminal = VirtualTerminal(columns=140, rows=40)
    screen = Screen(terminal)

    forbidden_patterns = ["//", "\\\\", "||"]
    scales = [(1, 1), (2, 1), (2, 2), (4, 2)]
    radius = 12

    for scale_idx, scale in enumerate(scales):
        arena.scale_index = scale_idx
        scale_w, scale_h = scale
        center_col = terminal.columns // 2
        center_row = terminal.rows // 2
        player_col_start = center_col
        player_col_end = center_col + scale_w
        player_row_start = center_row
        player_row_end = center_row + scale_h

        for deg in range(0, 360, 5):
            rad = math.radians(deg)
            target_x = int(arena.player.x + radius * math.cos(rad))
            target_y = int(arena.player.y + radius * math.sin(rad))

            arena.crosshair = Point(target_x, target_y)
            arena.fire()
            assert arena.shot_ray is not None

            screen.clear()
            arena.draw(screen)

            # Inspect all rows outside the player's own sprite footprint for forbidden patterns
            for row_index in range(terminal.rows):
                is_player_row = player_row_start <= row_index < player_row_end
                row_str = "".join(
                    screen.back_buffer.cells[row_index][col].char
                    for col in range(terminal.columns)
                    if not (is_player_row and player_col_start <= col < player_col_end)
                )
                for pattern in forbidden_patterns:
                    assert pattern not in row_str, (
                        f"Forbidden pattern '{pattern}' found at scale {scale}, angle {deg}° in row {row_index}: {row_str}"
                    )

            # Inspect all columns for vertically stacked diagonal slashes ('\\n\\' or '/\n/')
            for col in range(terminal.columns):
                for row_idx in range(terminal.rows - 1):
                    if player_col_start <= col < player_col_end and player_row_start <= row_idx < player_row_end:
                        continue
                    if player_col_start <= col < player_col_end and player_row_start <= row_idx + 1 < player_row_end:
                        continue
                    c1 = screen.back_buffer.cells[row_idx][col].char
                    c2 = screen.back_buffer.cells[row_idx + 1][col].char
                    assert not (c1 == "\\" and c2 == "\\"), (
                        f"Vertical forbidden '\\\\n\\\\' at scale {scale}, angle {deg}°, col {col}, row {row_idx}"
                    )
                    assert not (c1 == "/" and c2 == "/"), (
                        f"Vertical forbidden '/\\\\n/' at scale {scale}, angle {deg}°, col {col}, row {row_idx}"
                    )


def test_shot_ray_hit_marker_always_on_top_left_dot() -> None:
    """
    Verifies that the impact hit marker '*' is always placed at the top-left
    corner (col 0, row 0) of the target tile across all scales, directly replacing
    the floor dot '.'.
    """
    terminal = VirtualTerminal(columns=140, rows=40)
    screen = Screen(terminal)

    arena = Arena(map_name="Empty Proving Ground")
    arena.raytracing_enabled = False
    arena.shooting = True

    scales = [(1, 1), (2, 1), (2, 2), (4, 2)]
    for scale_idx, scale in enumerate(scales):
        arena.scale_index = scale_idx
        scale_w, scale_h = scale

        # Shoot in multiple directions (right, left, down, up, diagonals)
        for offset_x, offset_y in [(5, 0), (-5, 0), (0, 5), (0, -5), (4, 4), (-4, -4)]:
            arena.crosshair = Point(arena.player.x + offset_x, arena.player.y + offset_y)
            arena.fire()

            screen.clear()
            arena.draw(screen)

            center_col = terminal.columns // 2
            center_row = terminal.rows // 2
            origin_x = center_col - arena.player.x * scale_w
            origin_y = center_row - arena.player.y * scale_h

            expected_hit_x = origin_x + arena.crosshair.x * scale_w
            expected_hit_y = origin_y + arena.crosshair.y * scale_h

            assert screen.back_buffer.cells[expected_hit_y][expected_hit_x].char == "*", (
                f"Hit marker '*' not placed at top-left of target tile for scale {scale}, offset ({offset_x}, {offset_y})"
            )


def test_arena_fire_and_trail_modes() -> None:
    arena = Arena()
    arena.crosshair = Point(arena.player.x + 3, arena.player.y)
    assert arena.shot_ray is None

    # Fire weapon
    arena.fire()
    assert arena.shot_ray is not None
    assert arena.shot_ray.start == Point(arena.player.x, arena.player.y)
    assert arena.shot_ray.hit == arena.crosshair
    assert arena.shot_timer == 0.15

    # Timed mode: timer decreases and clears trail on expiration
    arena.update(0.10, Size(100, 40))
    assert arena.shot_ray is not None
    arena.update(0.06, Size(100, 40))
    assert arena.shot_ray is None

    # Turn-based mode (trail_timed = False)
    arena.trail_timed = False
    arena.fire()
    assert arena.shot_ray is not None

    # Passive time update does NOT clear turn-based trail
    arena.update(1.0, Size(100, 40))
    assert arena.shot_ray is not None

    # Input movement clears turn-based trail
    arena.dx = 1
    arena.update(0.016, Size(100, 40))
    assert arena.shot_ray is None


def test_arena_shot_trail_draw() -> None:
    arena = Arena()
    arena.shooting = True
    arena.crosshair = Point(arena.player.x + 4, arena.player.y)
    arena.fire()
    assert arena.shot_ray is not None

    terminal = VirtualTerminal(columns=140, rows=40)
    screen = Screen(terminal)
    arena.draw(screen)

    center_col = screen.size.columns // 2
    center_row = screen.size.rows // 2

    # Player is centered at center_col, center_row
    # Beam extends from player at center_col to hit at center_col + 4
    # Reticle left bracket is at center_col + 3
    # Hit cell is at center_col + 4
    # Reticle right bracket is at center_col + 5
    assert screen.back_buffer.cells[center_row][center_col].char == "☺"
    assert screen.back_buffer.cells[center_row][center_col + 1].char == "-"
    assert screen.back_buffer.cells[center_row][center_col + 2].char == "-"
    assert screen.back_buffer.cells[center_row][center_col + 3].char == "["
    assert screen.back_buffer.cells[center_row][center_col + 4].char == "*"
    assert screen.back_buffer.cells[center_row][center_col + 5].char == "]"


def test_virtual_input_handler_mouse() -> None:
    handler = VirtualInputHandler()
    assert handler.mouse_position is None
    assert not handler.mouse_pressed
    assert not handler.mouse_just_pressed

    # Hover mouse at (15, 25)
    handler.set_mouse_position(Point(15, 25))
    handler.update()
    assert handler.mouse_position == Point(15, 25)
    assert not handler.mouse_pressed
    assert not handler.mouse_just_pressed

    # Press left mouse button
    handler.press_mouse(1)
    handler.update()
    assert handler.mouse_pressed
    assert handler.mouse_just_pressed

    # Held down on second frame: pressed is True, just_pressed is False
    handler.update()
    assert handler.mouse_pressed
    assert not handler.mouse_just_pressed

    # Release button
    handler.release_mouse(1)
    handler.update()
    assert not handler.mouse_pressed
    assert not handler.mouse_just_pressed


def test_arena_mouse_aiming_and_shooting() -> None:
    arena = Arena()
    handler = VirtualInputHandler()
    screen_size = Size(140, 40)
    arena.update(0.016, screen_size)

    # Initial state
    assert not arena.shooting
    assert arena.shot_ray is None

    # Hovering over tile (player.x + 3, player.y + 2)
    target_screen_pt = arena.tile_to_screen(arena.player.x + 3, arena.player.y + 2)
    handler.set_mouse_position(target_screen_pt)
    handler.update()
    arena.handle_input(handler)

    assert arena.crosshair == Point(arena.player.x + 3, arena.player.y + 2)
    assert not arena.shooting

    # Right click toggles aiming mode
    handler.click_mouse(button=2)
    handler.update()
    arena.handle_input(handler)
    assert arena.shooting

    handler.release_mouse(button=2)
    handler.update()

    # Left click fires immediately and updates crosshair
    target_fire_tile = Point(arena.player.x + 4, arena.player.y)
    fire_screen_pt = arena.tile_to_screen(target_fire_tile.x, target_fire_tile.y)
    handler.set_mouse_position(fire_screen_pt)
    handler.press_mouse(button=1)
    handler.update()
    arena.handle_input(handler)

    assert arena.crosshair == target_fire_tile
    assert arena.shooting
    assert arena.shot_ray is not None
    assert arena.shot_ray.hit == target_fire_tile

    # Clicks on the status bar (rows 38 and 39) must be ignored
    handler.release_mouse(button=1)
    handler.update()
    arena.shot_ray = None

    status_bar_pt = Point(70, screen_size.rows - 2)
    handler.set_mouse_position(status_bar_pt)
    handler.press_mouse(button=1)
    handler.update()
    arena.handle_input(handler)
    # Target not altered and no fire triggered
    assert arena.shot_ray is None


def test_arena_colosseum_diagonal_visibility_and_firing() -> None:
    """
    Verifies that visible floor tiles past pillar corners (such as (25, 12) from (30, 15))
    can be fired at directly without premature obstacle collision, while shooting into the
    wall behind it (24, 11) lands at the same floor tile (25, 12).
    """
    arena = Arena(map_name="Colosseum Arena")
    assert arena.player.x == 30 and arena.player.y == 15

    # (25, 12) is visible in FOV
    assert Point(25, 12) in arena.visible_cells
    assert not arena.tilemap.is_opaque(25, 12)

    # Shooting directly at (25, 12) reaches target tile
    shot_open = trace_shot_ray(30, 15, 25, 12, arena.tilemap.is_opaque, arena.player.view_distance)
    assert shot_open.hit == Point(25, 12)
    assert not shot_open.is_impact

    # Shooting at wall behind it (24, 11) stops on open floor cell (25, 12)
    assert arena.tilemap.is_opaque(24, 11)
    shot_wall = trace_shot_ray(30, 15, 24, 11, arena.tilemap.is_opaque, arena.player.view_distance)
    assert shot_wall.hit == Point(25, 12)
    assert shot_wall.is_impact
