"""
Unit tests for interactive Arena state, SelectionTexture framing, and map cycling.
"""
from sanctuary.core.geometry import Point, Size
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
    cycle_next_map,
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
