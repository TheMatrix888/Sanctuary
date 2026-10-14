"""
Procedural map generators and preset definitions for the Arena scene.
Provides mathematical architectures for colosseums, bastions, chasms, ruins, and proving grounds.
"""
from collections.abc import Callable
from dataclasses import dataclass

from sanctuary.scenes.arena.tile_map import TileMap
from sanctuary.scenes.arena.tiles import (
    BLOOD_FLOOR,
    CHASM,
    FLOOR,
    WALL,
    Tile,
)


def generate_colosseum(width: int = 41, height: int = 41) -> TileMap:
    """Classic colosseum: concentric colonnade pillars and central blood-stained floor."""
    half_width = width // 2
    half_height = height // 2
    internal_radius = 5
    external_radius = 10

    tiles: list[list[Tile]] = []
    for relative_y in range(half_height, -half_height - height % 2, -1):
        row: list[Tile] = []
        for relative_x in range(-half_width, half_width + width % 2):
            is_boundary = (
                relative_x == -half_width
                or relative_x == half_width
                or relative_y == -half_height
                or relative_y == half_height
            )
            # Factor of 2 on relative_y compensates for terminal glyph aspect ratio (~1:2 width:height)
            aspect_distance_squared = relative_x ** 2 + relative_y ** 2 * 2
            is_colonnade_pillar = (
                external_radius ** 2 >= aspect_distance_squared >= internal_radius ** 2
            ) and (relative_y % 2 == 0)
            is_blood_floor = aspect_distance_squared < internal_radius ** 2

            if is_boundary or is_colonnade_pillar:
                row.append(WALL)
            elif is_blood_floor:
                row.append(BLOOD_FLOOR)
            else:
                row.append(FLOOR)
        tiles.append(row)

    return TileMap(width=width, height=height, tiles=tiles)


def generate_concentric_bastions(width: int = 41, height: int = 41) -> TileMap:
    """Concentric modular rings (radius % 4 == 0) with axial and diagonal passage gates."""
    half_width = width // 2
    half_height = height // 2

    tiles: list[list[Tile]] = []
    for relative_y in range(half_height, -half_height - height % 2, -1):
        row: list[Tile] = []
        for relative_x in range(-half_width, half_width + width % 2):
            is_boundary = (
                relative_x == -half_width
                or relative_x == half_width
                or relative_y == -half_height
                or relative_y == half_height
            )
            # Factor of 2 on relative_y compensates for terminal glyph aspect ratio (~1:2 width:height)
            aspect_distance_squared = relative_x ** 2 + relative_y ** 2 * 2
            aspect_radius = int(aspect_distance_squared ** 0.5)

            is_ring = (3 <= aspect_radius <= min(half_width, half_height * 2) - 2) and (aspect_radius % 4 == 0)
            is_passage_gate = (
                relative_x == 0
                or relative_y == 0
                or abs(relative_x) == abs(relative_y * 2)
                or abs(relative_x) == abs(relative_y * 2 + 1)
            )
            is_blood_floor = aspect_radius < 3

            if is_boundary:
                row.append(WALL)
            elif is_ring and not is_passage_gate:
                row.append(WALL)
            elif is_blood_floor:
                row.append(BLOOD_FLOOR)
            else:
                row.append(FLOOR)
        tiles.append(row)

    return TileMap(width=width, height=height, tiles=tiles)


def generate_greek_amphitheater(width: int = 41, height: int = 41) -> TileMap:
    """Elliptical outer colosseum bowl with regular classical column spacing."""
    half_width = width // 2
    half_height = height // 2

    tiles: list[list[Tile]] = []
    for relative_y in range(half_height, -half_height - height % 2, -1):
        row: list[Tile] = []
        for relative_x in range(-half_width, half_width + width % 2):
            normalized_x = relative_x / max(half_width - 1, 1)
            normalized_y = relative_y / max(half_height - 1, 1)
            ellipse_distance = normalized_x ** 2 + normalized_y ** 2

            # Factor of 2 on relative_y compensates for terminal glyph aspect ratio (~1:2 width:height)
            aspect_distance_squared = relative_x ** 2 + relative_y ** 2 * 2

            is_boundary = ellipse_distance >= 1.0
            is_classical_column = (
                (aspect_distance_squared >= 25)
                and (relative_x % 3 == 0)
                and (relative_y % 2 == 0)
                and (ellipse_distance < 0.85)
            )
            is_blood_floor = aspect_distance_squared < 9

            if is_boundary or is_classical_column:
                row.append(WALL)
            elif is_blood_floor:
                row.append(BLOOD_FLOOR)
            else:
                row.append(FLOOR)
        tiles.append(row)

    return TileMap(width=width, height=height, tiles=tiles)


def generate_tectonic_chasm(width: int = 41, height: int = 41) -> TileMap:
    """Divided arena split by an impassable yet transparent abyss with crossing bridges."""
    half_width = width // 2
    half_height = height // 2

    tiles: list[list[Tile]] = []
    for relative_y in range(half_height, -half_height - height % 2, -1):
        row: list[Tile] = []
        for relative_x in range(-half_width, half_width + width % 2):
            is_boundary = (
                relative_x == -half_width
                or relative_x == half_width
                or relative_y == -half_height
                or relative_y == half_height
            )

            # Chasm runs vertically through relative_x in [-1, 1]
            is_chasm_channel = -1 <= relative_x <= 1
            # Three crossing bridges: center, top, bottom
            is_crossing_bridge = (
                (abs(relative_y) <= 1)
                or (abs(relative_y - (half_height - 3)) <= 1)
                or (abs(relative_y - (-half_height + 3)) <= 1)
            )

            # Defensive cover pillars on either side of the chasm
            is_cover_pillar = abs(relative_x) == 5 and relative_y % 3 == 0
            is_blood_floor = relative_x == 0 and relative_y == 0

            if is_boundary or is_cover_pillar:
                row.append(WALL)
            elif is_chasm_channel and not is_crossing_bridge:
                row.append(CHASM)
            elif is_blood_floor:
                row.append(BLOOD_FLOOR)
            else:
                row.append(FLOOR)
        tiles.append(row)

    return TileMap(width=width, height=height, tiles=tiles)


def generate_sierpinski_ruins(width: int = 41, height: int = 41) -> TileMap:
    """Deterministic mathematical labyrinth driven by modular bitwise XOR logic."""
    half_width = width // 2
    half_height = height // 2

    tiles: list[list[Tile]] = []
    for relative_y in range(half_height, -half_height - height % 2, -1):
        row: list[Tile] = []
        for relative_x in range(-half_width, half_width + width % 2):
            is_boundary = (
                relative_x == -half_width
                or relative_x == half_width
                or relative_y == -half_height
                or relative_y == half_height
            )
            # Factor of 2 on relative_y compensates for terminal glyph aspect ratio (~1:2 width:height)
            aspect_distance_squared = relative_x ** 2 + relative_y ** 2 * 2

            xor_pattern_value = ((relative_x + half_width) ^ ((relative_y + half_height) * 2)) % 5
            is_ruin_wall = (aspect_distance_squared >= 16) and (xor_pattern_value == 0)
            is_blood_floor = aspect_distance_squared < 9

            if is_boundary or is_ruin_wall:
                row.append(WALL)
            elif is_blood_floor:
                row.append(BLOOD_FLOOR)
            else:
                row.append(FLOOR)
        tiles.append(row)

    return TileMap(width=width, height=height, tiles=tiles)


def generate_proving_ground(width: int = 41, height: int = 41) -> TileMap:
    """Clean open sparring square: outer walls and central blood ring, zero obstacles."""
    half_width = width // 2
    half_height = height // 2

    tiles: list[list[Tile]] = []
    for relative_y in range(half_height, -half_height - height % 2, -1):
        row: list[Tile] = []
        for relative_x in range(-half_width, half_width + width % 2):
            is_boundary = (
                relative_x == -half_width
                or relative_x == half_width
                or relative_y == -half_height
                or relative_y == half_height
            )
            # Factor of 2 on relative_y compensates for terminal glyph aspect ratio (~1:2 width:height)
            aspect_distance_squared = relative_x ** 2 + relative_y ** 2 * 2
            is_blood_floor = aspect_distance_squared < 9

            if is_boundary:
                row.append(WALL)
            elif is_blood_floor:
                row.append(BLOOD_FLOOR)
            else:
                row.append(FLOOR)
        tiles.append(row)

    return TileMap(width=width, height=height, tiles=tiles)


@dataclass(slots=True, frozen=True)
class ArenaPreset:
    """Declarative definition of a selectable arena generation preset."""
    name: str
    generator: Callable[[int, int], TileMap]


ARENA_PRESETS: list[ArenaPreset] = [
    ArenaPreset("Colosseum Arena", generate_colosseum),
    ArenaPreset("Concentric Bastions", generate_concentric_bastions),
    ArenaPreset("Greek Amphitheater", generate_greek_amphitheater),
    ArenaPreset("Tectonic Chasm", generate_tectonic_chasm),
    ArenaPreset("Sierpinski Ruins", generate_sierpinski_ruins),
    ArenaPreset("Empty Proving Ground", generate_proving_ground),
]
