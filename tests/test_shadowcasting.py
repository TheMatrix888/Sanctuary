"""
Unit tests for 8-octant discrete shadowcasting algorithm in sanctuary/core/shadowcasting.py.
"""
from sanctuary.core.geometry import Point
from sanctuary.core.shadowcasting import field_of_view, octant_shadowcast, OCTANTS


def test_field_of_view_empty_room() -> None:
    # In an empty room, every cell within radius should be visible
    center = Point(10, 10)
    visible = field_of_view(center, view_distance=5, is_opaque=lambda x, y: False)

    assert center in visible
    assert visible[center] == 4

    # Cells immediately adjacent in all 8 directions
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            pt = Point(center.x + dx, center.y + dy)
            assert pt in visible
            assert 1 <= visible[pt] <= 4

    # Distance beyond view_distance shouldn't be reached
    assert Point(10, 16) not in visible
    assert Point(16, 10) not in visible


def test_field_of_view_wall_occlusion() -> None:
    # Wall placed directly East at (12, 10), center at (10, 10)
    walls = {Point(12, 10)}
    center = Point(10, 10)

    visible = field_of_view(
        center,
        view_distance=5,
        is_opaque=lambda x, y: Point(x, y) in walls,
    )

    # Floor between center and wall is visible
    assert Point(11, 10) in visible
    # Wall itself is visible
    assert Point(12, 10) in visible
    # Cell directly behind wall is in shadow
    assert Point(13, 10) not in visible
    assert Point(14, 10) not in visible


def test_octant_shadowcast_early_exit() -> None:
    # When immediately adjacent wall blocks entire octant
    center = Point(0, 0)
    # Block immediately at x=1
    visible = octant_shadowcast(
        center,
        view_distance=10,
        is_opaque=lambda x, y: True,
        octant=OCTANTS[0],
    )
    # Only the first layer of walls should be recorded
    assert Point(0, 1) in visible or Point(1, 0) in visible
    # Far points in this octant should not be reached due to early break
    assert Point(0, 10) not in visible


COLOSSEUM_SPAWN_FOV_SNAPSHOT = [
    "                     ",  # y=5
    "                     ",  # y=6
    "                     ",  # y=7
    "                     ",  # y=8
    "                     ",  # y=9
    "                     ",  # y=10
    "    #############    ",  # y=11
    "    .............    ",  # y=12
    ".#####.........#####.",  # y=13
    ".....................",  # y=14
    "     #....@....#     ",  # y=15
    ".....................",  # y=16
    ".#####.........#####.",  # y=17
    "    .............    ",  # y=18
    "    #############    ",  # y=19
    "                     ",  # y=20
    "                     ",  # y=21
    "                     ",  # y=22
    "                     ",  # y=23
    "                     ",  # y=24
    "                     ",  # y=25
]


def test_colosseum_spawn_ascii_snapshot() -> None:
    """
    Visual Golden Master snapshot test for Colosseum arena spawn.
    Renders character-by-character ASCII screenshot of the player's 360-degree field of view
    from spawn coordinates (30, 15) with view_distance=10.
    Guarantees strict geometric invariance: zero holes, zero light leaks, and exact symmetry.
    """
    from sanctuary.scenes.arena import Arena

    arena = Arena(map_name="Colosseum Arena")
    center = Point(arena.player.x, arena.player.y)
    assert center == Point(30, 15)
    assert arena.player.view_distance == 10

    actual_rows: list[str] = []
    for y in range(5, 26):
        line_chars: list[str] = []
        for x in range(20, 41):
            pt = Point(x, y)
            if pt == center:
                line_chars.append("@")
            elif pt in arena.visible_cells:
                line_chars.append("#" if arena.tilemap.is_opaque(x, y) else ".")
            else:
                line_chars.append(" ")
        actual_rows.append("".join(line_chars))

    for idx, (expected_line, actual_line) in enumerate(zip(COLOSSEUM_SPAWN_FOV_SNAPSHOT, actual_rows)):
        y_coord = idx + 5
        assert actual_line == expected_line, (
            f"Colosseum FOV snapshot mismatch at y={y_coord}:\n"
            f"Expected: {repr(expected_line)}\n"
            f"Actual:   {repr(actual_line)}"
        )

