"""
Interactive tactical arena sandbox with discrete raytracing and procedural presets.
"""
from dataclasses import dataclass

from sanctuary.core.geometry import Point, Size, field_of_view
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Pop, State, ToggleMetrics
from sanctuary.scenes.arena.generators import ARENA_PRESETS
from sanctuary.scenes.arena.map import ArenaMap
from sanctuary.scenes.arena.tiles import Tile, get_tile_render

ARENA_WIDTH = 41
ARENA_HEIGHT = 41


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
    Interactive arena state supporting discrete player exploration, 360-degree FOV,
    preset cycling (Tab), and god-view / raytracing toggle (F1).
    """
    arena_map: ArenaMap
    player: Entity
    visible_cells: set[Point]
    preset_index: int
    raytracing_enabled: bool

    def __init__(self) -> None:
        self.preset_index = 0
        self.raytracing_enabled = True
        self.reset()

    def reset(self, preset_index: int | None = None) -> None:
        if preset_index is not None:
            self.preset_index = preset_index % len(ARENA_PRESETS)

        preset = ARENA_PRESETS[self.preset_index]
        self.arena_map = preset.generator(ARENA_WIDTH, ARENA_HEIGHT)

        self.player = Entity(
            x=ARENA_WIDTH // 2,
            y=ARENA_HEIGHT // 2,
            dx=0,
            dy=0,
            view_distance=10,
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
        # Movement controls
        if input_handler.just_pressed(Key.RIGHT) or input_handler.just_pressed(Key.D):
            self.player.dx += 1
        if input_handler.just_pressed(Key.LEFT) or input_handler.just_pressed(Key.A):
            self.player.dx -= 1
        if input_handler.just_pressed(Key.UP) or input_handler.just_pressed(Key.W):
            self.player.dy -= 1
        if input_handler.just_pressed(Key.DOWN) or input_handler.just_pressed(Key.S):
            self.player.dy += 1

        # Preset cycling (Tab)
        if input_handler.just_pressed(Key.TAB):
            self.reset(self.preset_index + 1)

        # Vision toggle (F1)
        if input_handler.just_pressed(Key.F1):
            self.raytracing_enabled = not self.raytracing_enabled

        # Lifecycle navigation
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
        camera_offset_x = screen.size.columns // 2 - self.player.x
        camera_offset_y = screen.size.rows // 2 - self.player.y

        if self.raytracing_enabled:
            # Raytracing mode: render only illuminated cells within circular FOV
            for point in self.visible_cells:
                tile = self.arena_map.get_tile(point.x, point.y)
                if tile != Tile.EMPTY:
                    tile_glyph, tile_color = get_tile_render(tile)
                    screen.draw_text(
                        point.x + camera_offset_x,
                        point.y + camera_offset_y,
                        tile_glyph,
                        fg_color=tile_color,
                    )
        else:
            # Full map view (F1 toggle / god view): render entire arena without FOV
            for y in range(self.arena_map.height):
                for x in range(self.arena_map.width):
                    tile = self.arena_map.get_tile(x, y)
                    if tile != Tile.EMPTY:
                        tile_glyph, tile_color = get_tile_render(tile)
                        screen.draw_text(
                            x + camera_offset_x,
                            y + camera_offset_y,
                            tile_glyph,
                            fg_color=tile_color,
                        )

        # Draw player entity in center of screen
        screen.draw_text(
            screen.size.columns // 2,
            screen.size.rows // 2,
            self.player.glyph,
            self.player.fg_color,
        )

        # Bottom status bar with preset and vision mode telemetry
        current_preset = ARENA_PRESETS[self.preset_index]
        vision_mode = "Raytracing" if self.raytracing_enabled else "Full Map"
        status_text = (
            f"x: {self.player.x} y: {self.player.y} | "
            f"[Tab] Preset: {current_preset.name} | "
            f"[F1] Vision: {vision_mode}"
        )
        screen.draw_text(
            0,
            screen.size.rows - 1,
            status_text.ljust(screen.size.columns),
            bg_color=Color(48, 48, 48),
        )
