"""
Interactive tactical arena sandbox with discrete raytracing, procedural presets,
and multi-resolution Texture rendering (1x1, 2x1, 4x2).
"""
from sanctuary.core.geometry import Point, Size, field_of_view
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Pop, State, ToggleMetrics
from .config import ARENA_HEIGHT, ARENA_WIDTH, ZOOM_SCALES
from .entities import Entity, create_player
from .generators import ARENA_PRESETS
from .tile_map import TileMap


class Arena(State):
    """
    Interactive arena state supporting discrete player exploration, 360-degree FOV,
    preset cycling (Tab), god-view toggle (F1), and multi-LOD scaling (F2).
    """
    tilemap: TileMap
    player: Entity
    player_dx: int
    player_dy: int
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
        self.preset_index = preset_index % len(ARENA_PRESETS)
        generator = list(ARENA_PRESETS.values())[self.preset_index]
        self.tilemap = generator(ARENA_WIDTH, ARENA_HEIGHT)

        self.player = create_player(
            ARENA_WIDTH // 2,
            ARENA_HEIGHT // 2,
            10,
            100,
            100
        )
        self.player_dx = 0
        self.player_dy = 0

        self.update_fov()

    def on_enter(self) -> None:
        self.reset()

    def update_fov(self) -> None:
        """Recalculates player line-of-sight visibility cache."""
        self.visible_cells = field_of_view(
            self.player.x,
            self.player.y,
            self.player.view_distance,
            self.tilemap.is_opaque,
        )

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        # Movement controls
        if input_handler.is_repeated(Key.RIGHT, Key.D):
            self.player_dx += 1
        if input_handler.is_repeated(Key.LEFT, Key.A):
            self.player_dx -= 1
        if input_handler.is_repeated(Key.UP, Key.W):
            self.player_dy -= 1
        if input_handler.is_repeated(Key.DOWN, Key.S):
            self.player_dy += 1

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
        if self.player_dx != 0 and self.player_dy != 0:
            # Diagonal movement attempt: enforce strict corner collision check (supercover raycasting parity).
            # Both orthogonal intermediate steps and the target cell must be walkable to prevent diagonal clipping.
            can_x = self.tilemap.is_walkable(self.player.x + self.player_dx, self.player.y)
            can_y = self.tilemap.is_walkable(self.player.x, self.player.y + self.player_dy)
            target = self.tilemap.is_walkable(self.player.x + self.player_dx, self.player.y + self.player_dy)

            if can_x and can_y and target:
                self.player.x += self.player_dx
                self.player.y += self.player_dy
                self.update_fov()
            self.player_dx = 0
            self.player_dy = 0
        elif self.player_dx != 0 or self.player_dy != 0:
            target_x = self.player.x + self.player_dx
            target_y = self.player.y + self.player_dy
            if self.tilemap.is_walkable(target_x, target_y):
                self.player.x = target_x
                self.player.y = target_y
                self.update_fov()
            self.player_dx = 0
            self.player_dy = 0

    def draw(self, screen: Screen) -> None:
        scale_w, scale_h = self.tile_scale
        center_col = screen.size.columns // 2
        center_row = screen.size.rows // 2

        origin_x = center_col - self.player.x * scale_w
        origin_y = center_row - self.player.y * scale_h
        visible = self.visible_cells if self.raytracing_enabled else None
        self.tilemap.draw(screen, origin_x, origin_y, scale=self.tile_scale, visible_cells=visible)
        self.player.draw(screen, origin_x, origin_y, scale=self.tile_scale, transparent_space=True)

        # Bottom status bar with scale, vision mode, and preset telemetry
        vision_mode = "Raytracing" if self.raytracing_enabled else "Full Map"
        scale_label = f"{scale_w}x{scale_h}"
        status_text = (
            f"x: {self.player.x:2d} y: {self.player.y:2d} | "
            f"[Tab] Scale: {scale_label} | "
            f"[F1] {vision_mode} | "
            f"[F2] change preset"
        )
        screen.draw_text(
            0,
            screen.size.rows - 1,
            status_text.ljust(screen.size.columns)[:screen.size.columns],
            bg_color=Color(48, 48, 48),
        )
