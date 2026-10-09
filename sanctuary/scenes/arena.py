"""
Interactive tactical arena sandbox with 4-connected discrete raytracing and dynamic FOV.
"""
from dataclasses import dataclass
from enum import IntFlag

from sanctuary.core.geometry import Point, Size, field_of_view
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import State, Command, Pop, ToggleMetrics

ARENA_WIDTH = 41
ARENA_HEIGHT = 41


class Tile(IntFlag):
    """Bitmask properties of discrete map cells."""
    EMPTY = 0
    WALKABLE = 1 << 0   # Physical entities can step onto this cell
    OPAQUE = 1 << 1     # Blocks line-of-sight and light propagation
    BLOOD = 1 << 2


FLOOR = Tile.WALKABLE
WALL = Tile.OPAQUE
BLOOD = Tile.WALKABLE | Tile.BLOOD


@dataclass(slots=True)
class ArenaMap:
    """Discrete tile grid representing the arena layout and material properties."""
    width: int
    height: int
    tiles: list[list[Tile]]

    def is_opaque(self, x: int, y: int) -> bool:
        """Determines if a cell blocks vision. Out-of-bounds cells are opaque."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return bool(self.tiles[y][x] & Tile.OPAQUE)
        return True

    def is_walkable(self, x: int, y: int) -> bool:
        """Determines if an entity can enter the cell. Out-of-bounds is non-walkable."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return bool(self.tiles[y][x] & Tile.WALKABLE)
        return False

    def get_tile(self, x: int, y: int) -> Tile:
        """Retrieves tile properties at the specified coordinate."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return Tile.EMPTY


def generate_arena() -> ArenaMap:
    """Generates the procedural arena layout with colosseum colonnades and sanctum."""
    internal_radius = 5
    external_radius = 10
    half_width = ARENA_WIDTH // 2
    half_height = ARENA_HEIGHT // 2

    tiles: list[list[Tile]] = []
    for y in range(half_height, -half_height - ARENA_HEIGHT % 2, -1):
        row: list[Tile] = []
        for x in range(-half_width, half_width + ARENA_WIDTH % 2):
            is_pillar = (external_radius ** 2 >= x ** 2 + y ** 2 * 2 >= internal_radius ** 2) and (y % 2 == 0)
            is_pillar = is_pillar or y == 10
            is_blood = (x ** 2 + y ** 2 * 2 < internal_radius ** 2)

            if is_pillar:
                row.append(WALL)
            elif is_blood:
                row.append(BLOOD)
            else:
                row.append(FLOOR)
        tiles.append(row)

    return ArenaMap(width=ARENA_WIDTH, height=ARENA_HEIGHT, tiles=tiles)


def get_tile_render(tile: Tile) -> tuple[str, Color]:
    """Resolves tile bitmask properties into display character and palette color."""
    if tile & Tile.OPAQUE:
        return "#", Color(192, 192, 192)
    if tile & Tile.BLOOD:
        return "·", Color(220, 60, 60)
    return "·", Color(64, 200, 64)


@dataclass(slots=True)
class Entity:
    """Entity representation in the arena."""
    x: int
    y: int
    dx: int
    dy: int
    view_distance: int
    glyph: str
    fg_color: Color | None = None


class Arena(State):
    """
    Interactive arena state supporting discrete player exploration with 360-degree FOV.
    """
    arena_map: ArenaMap
    player: Entity
    visible_cells: set[Point]

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.arena_map = generate_arena()
        self.player = Entity(
            x=ARENA_WIDTH // 2,
            y=ARENA_HEIGHT // 2,
            dx=0,
            dy=0,
            view_distance=8,
            glyph="☺",
            fg_color=Color(128, 0, 255),
        )
        self.update_fov()

    def on_enter(self) -> None:
        self.reset()

    def update_fov(self) -> None:
        """Recalculates player line-of-sight visibility cache."""
        self.visible_cells = field_of_view(
            self.player.x,
            self.player.y,
            self.player.view_distance,
            self.arena_map.is_opaque,
        )

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        if input_handler.just_pressed(Key.RIGHT) or input_handler.just_pressed(Key.D):
            self.player.dx += 1
        if input_handler.just_pressed(Key.LEFT) or input_handler.just_pressed(Key.A):
            self.player.dx -= 1
        if input_handler.just_pressed(Key.UP) or input_handler.just_pressed(Key.W):
            self.player.dy -= 1
        if input_handler.just_pressed(Key.DOWN) or input_handler.just_pressed(Key.S):
            self.player.dy += 1
        if input_handler.just_pressed(Key.ESC):
            return Pop()
        if input_handler.just_pressed(Key.F3):
            return ToggleMetrics()
        return None

    def update(self, dt: float, screen_size: Size) -> None:
        if self.player.dx != 0 or self.player.dy != 0:
            target_x = self.player.x + self.player.dx
            target_y = self.player.y + self.player.dy
            if self.arena_map.is_walkable(target_x, target_y):
                self.player.x = target_x
                self.player.y = target_y
                self.update_fov()
            self.player.dx = 0
            self.player.dy = 0

    def draw(self, screen: Screen) -> None:
        camera_x = screen.size.columns // 2 - self.player.x
        camera_y = screen.size.rows // 2 - self.player.y

        for point in self.visible_cells:
            tile = self.arena_map.get_tile(point.x, point.y)
            if tile != Tile.EMPTY:
                char, color = get_tile_render(tile)
                screen.draw_text(point.x + camera_x, point.y + camera_y, char, fg_color=color)

        screen.draw_text(screen.size.columns // 2, screen.size.rows // 2, self.player.glyph, self.player.fg_color)
        ui_text = f"x {self.player.x} y {self.player.y}"
        screen.draw_text(0, screen.size.rows - 1, ui_text.ljust(screen.size.columns), bg_color=Color(64, 64, 64))
