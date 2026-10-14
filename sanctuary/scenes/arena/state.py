"""
Interactive tactical arena sandbox with discrete raytracing, procedural presets,
and multi-resolution Texture rendering (1x1, 2x1, 4x2).
"""
from sanctuary.core.geometry import Point, Size, field_of_view
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Pop, State, ToggleMetrics
from sanctuary.scenes.arena.entities import Entity, create_player
from sanctuary.scenes.arena.generators import ARENA_PRESETS
from sanctuary.scenes.arena.tile_map import TileMap
from sanctuary.scenes.arena.tiles import EMPTY, Tile

ARENA_WIDTH = 41
ARENA_HEIGHT = 21

ZOOM_SCALES: list[tuple[int, int]] = [(1, 1), (2, 1), (2, 2), (4, 2)]


class Arena(State):
    """
    Interactive arena state supporting discrete player exploration, 360-degree FOV,
    preset cycling (Tab), god-view toggle (F1), and multi-LOD scaling (F2).
    """
    tile_map: TileMap
    player: Entity
    visible_cells: set[Point]
    preset_index: int
    scale_index: int
    raytracing_enabled: bool

    def __init__(self) -> None:
        self.preset_index = 0
        self.scale_index = 0
        self.raytracing_enabled = True
        self.reset()

    @property
    def tile_scale(self) -> tuple[int, int]:
        """Returns the active (width, height) cell footprint scale."""
        return ZOOM_SCALES[self.scale_index]

    def reset(self, preset_index: int = 0) -> None:
        if preset_index is not None:
            self.preset_index = preset_index % len(ARENA_PRESETS)

        preset = ARENA_PRESETS[self.preset_index]
        self.tile_map = preset.generator(ARENA_WIDTH, ARENA_HEIGHT)

        self.player = create_player(
            x=ARENA_WIDTH // 2,
            y=ARENA_HEIGHT // 2,
            view_distance=10,
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
            self.tile_map.is_opaque,
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

        # Footprint scale / zoom toggle (Tab)
        if input_handler.just_pressed(Key.TAB):
            self.scale_index = (self.scale_index + 1) % len(ZOOM_SCALES)

        # Vision toggle (F1)
        if input_handler.just_pressed(Key.F1):
            self.raytracing_enabled = not self.raytracing_enabled

        # Preset cycling (F2)
        if input_handler.just_pressed(Key.F2):
            self.reset(self.preset_index + 1)

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
            if self.tile_map.is_walkable(target_x, target_y):
                self.player.x = target_x
                self.player.y = target_y
                self.update_fov()
            self.player.dx = 0
            self.player.dy = 0

    def draw(self, screen: Screen) -> None:
        scale_w, scale_h = self.tile_scale
        center_col = screen.size.columns // 2
        center_row = screen.size.rows // 2

        if self.raytracing_enabled:
            # Raytracing mode: render only illuminated cells within circular FOV
            for point in self.visible_cells:
                tile = self.tile_map.get_tile(point.x, point.y)
                if tile != EMPTY:
                    screen_x = center_col + (point.x - self.player.x) * scale_w
                    screen_y = center_row + (point.y - self.player.y) * scale_h
                    surface = tile.texture.get_surface(self.tile_scale)
                    screen.draw_surface(screen_x, screen_y, surface)
        else:
            # Full map view (F1 toggle / god view): render entire arena without FOV
            for y in range(self.tile_map.height):
                for x in range(self.tile_map.width):
                    tile = self.tile_map.get_tile(x, y)
                    if tile != EMPTY:
                        screen_x = center_col + (x - self.player.x) * scale_w
                        screen_y = center_row + (y - self.player.y) * scale_h
                        surface = tile.texture.get_surface(self.tile_scale)
                        screen.draw_surface(screen_x, screen_y, surface)

        # Draw player entity in center of screen
        player_surface = self.player.texture.get_surface(self.tile_scale)
        screen.draw_surface(center_col, center_row, player_surface, transparent_space=True)

        # Bottom status bar with scale, vision mode, and preset telemetry
        current_preset = ARENA_PRESETS[self.preset_index]
        vision_mode = "Raytracing" if self.raytracing_enabled else "Full Map"
        scale_label = f"{scale_w}x{scale_h}"
        status_text = (
            f"x: {self.player.x:2d} y: {self.player.y:2d} | "
            f"[Tab] Scale: {scale_label} | "
            f"[F1] {vision_mode} | "
            f"[F2] {current_preset.name}"
        )
        screen.draw_text(
            0,
            screen.size.rows - 1,
            status_text.ljust(screen.size.columns)[:screen.size.columns],
            bg_color=Color(48, 48, 48),
        )
