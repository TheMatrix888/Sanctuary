"""
Interactive tactical arena sandbox with discrete raytracing, procedural presets,
and multi-resolution Texture rendering (1x1, 2x1, 4x2).
"""
from sanctuary.core.config import MIN_COLUMNS, MIN_ROWS
from sanctuary.core.geometry import Point, Size, field_of_view
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import Commands, Pop, State, ToggleMetrics
from .ballistics import ShotRay, draw_shot_ray, trace_shot_ray
from .config import ARENA_HEIGHT, ARENA_WIDTH, DEFAULT_MAP, ZOOM_SCALES
from .entities import Entity, create_player
from .generators import ARENA_PRESETS, cycle_next_map
from .textures import (
    RETICLE_AMBER_TEXTURE,
    RETICLE_RED_TEXTURE,
)
from .tile_map import TileMap


class Arena(State):
    """
    Interactive arena state supporting discrete player exploration, 360-degree FOV,
    map preset cycling (F2), god-view toggle (F1), and multi-LOD scaling (Tab).
    """
    map: str
    tilemap: TileMap
    player: Entity
    visible_cells: set[Point]
    scale_index: int
    raytracing_enabled: bool
    shooting: bool
    crosshair: Point
    dx: int
    dy: int
    shot_ray: ShotRay | None
    shot_timer: float
    trail_timed: bool
    screen_size: Size
    _last_mouse_pos: Point | None

    def __init__(self, map_name: str = DEFAULT_MAP) -> None:
        self.map = map_name
        self.scale_index = 0
        self.raytracing_enabled = True
        self.shooting = False
        self.crosshair = Point(0, 0)
        self.dx = 0
        self.dy = 0
        self.shot_ray = None
        self.shot_timer = 0.0
        self.trail_timed = True
        self.screen_size = Size(MIN_COLUMNS, MIN_ROWS)
        self._last_mouse_pos = None
        self.reset()

    @property
    def tile_scale(self) -> tuple[int, int]:
        """Returns the active (width, height) cell footprint scale."""
        return ZOOM_SCALES[self.scale_index]

    def reset(self, map_name: str | None = None) -> None:
        if map_name is not None and map_name in ARENA_PRESETS:
            self.map = map_name

        generator = ARENA_PRESETS[self.map]
        self.tilemap = generator(ARENA_WIDTH, ARENA_HEIGHT)

        self.player = create_player(
            ARENA_WIDTH // 2,
            ARENA_HEIGHT // 2,
            10,
            100,
            100,
        )
        self.crosshair = Point(self.player.x, max(0, self.player.y - 1))
        self.dx = 0
        self.dy = 0
        self.shot_ray = None
        self.shot_timer = 0.0

        self.update_fov()
        self.shooting = False

    def update_fov(self) -> None:
        """Recalculates player line-of-sight visibility cache."""
        self.visible_cells = field_of_view(
            self.player.x,
            self.player.y,
            self.player.view_distance,
            self.tilemap.is_opaque,
        )

    def screen_to_tile(self, screen_col: int, screen_row: int) -> Point:
        """Converts screen character cell coordinates to arena tile coordinates."""
        scale_w, scale_h = self.tile_scale
        center_col = self.screen_size.columns // 2
        center_row = self.screen_size.rows // 2
        origin_x = center_col - self.player.x * scale_w
        origin_y = center_row - self.player.y * scale_h
        return Point((screen_col - origin_x) // scale_w, (screen_row - origin_y) // scale_h)

    def tile_to_screen(self, tile_x: int, tile_y: int) -> Point:
        """Converts arena tile coordinates to top-left screen character cell coordinates."""
        scale_w, scale_h = self.tile_scale
        center_col = self.screen_size.columns // 2
        center_row = self.screen_size.rows // 2
        origin_x = center_col - self.player.x * scale_w
        origin_y = center_row - self.player.y * scale_h
        return Point(origin_x + tile_x * scale_w, origin_y + tile_y * scale_h)

    def fire(self, force: bool = False) -> bool:
        """Traces and renders a ballistic projectile beam toward the crosshair if visible in FOV."""
        if not force and self.raytracing_enabled and self.crosshair not in self.visible_cells:
            return False

        self.shot_ray = trace_shot_ray(
            self.player.x,
            self.player.y,
            self.crosshair.x,
            self.crosshair.y,
            self.tilemap.is_opaque,
            self.player.view_distance
        )
        if self.trail_timed:
            self.shot_timer = 0.15
        return True

    def handle_input(self, input_handler: InputHandler) -> Commands:
        # Mouse aiming and shooting
        if input_handler.mouse_position is not None:
            col = input_handler.mouse_position.x
            row = input_handler.mouse_position.y
            if row < self.screen_size.rows - 2:
                hovered_tile = self.screen_to_tile(col, row)
                if 0 <= hovered_tile.x < ARENA_WIDTH and 0 <= hovered_tile.y < ARENA_HEIGHT:
                    if input_handler.mouse_position != self._last_mouse_pos:
                        self._last_mouse_pos = input_handler.mouse_position
                        self.crosshair = hovered_tile

                    if input_handler.mouse_just_pressed:
                        self.crosshair = hovered_tile
                        self.shooting = True
                        self.fire()
                    elif input_handler.mouse_right_just_pressed:
                        self.crosshair = hovered_tile
                        self.shooting = not self.shooting

        # Directional navigation controls (shared vector for movement and aiming)
        if input_handler.is_repeated(Key.RIGHT, Key.D):
            self.dx += 1
        if input_handler.is_repeated(Key.LEFT, Key.A):
            self.dx -= 1
        if input_handler.is_repeated(Key.UP, Key.W):
            self.dy -= 1
        if input_handler.is_repeated(Key.DOWN, Key.S):
            self.dy += 1

        # Footprint scale / zoom toggle (Tab)
        if input_handler.just_pressed(Key.TAB):
            self.scale_index = (self.scale_index + 1) % len(ZOOM_SCALES)

        # Vision toggle (F1)
        if input_handler.just_pressed(Key.F1):
            self.raytracing_enabled = not self.raytracing_enabled

        # Map preset cycling (F2)
        if input_handler.just_pressed(Key.F2):
            self.reset(cycle_next_map(self.map))

        # Trail mode toggle (F4: Timed vs Turn-based)
        if input_handler.just_pressed(Key.F4):
            self.trail_timed = not self.trail_timed

        # Weapon discharge (Space or F when aiming)
        if self.shooting and input_handler.just_pressed(Key.SPACE, Key.F):
            self.fire()

        # Shooting toggle (Enter)
        if input_handler.just_pressed(Key.ENTER):
            self.shooting = not self.shooting
            self.dx = 0
            self.dy = 0
            if self.shooting:
                self.crosshair = Point(self.player.x, self.player.y)

        # Lifecycle navigation
        if input_handler.just_pressed(Key.ESC):
            return Pop()
        if input_handler.just_pressed(Key.F3):
            return ToggleMetrics()

        return None

    def update(self, dt: float, screen_size: Size) -> None:
        self.screen_size = screen_size

        # Clear turn-based trail on input deltas
        if not self.trail_timed and (self.dx != 0 or self.dy != 0):
            self.shot_ray = None

        # Countdown timed fade trail
        if self.trail_timed and self.shot_timer > 0:
            self.shot_timer -= dt
            if self.shot_timer <= 0:
                self.shot_ray = None

        if self.shooting:
            if self.dx != 0 or self.dy != 0:
                target_x = self.crosshair.x + self.dx
                target_y = self.crosshair.y + self.dy
                if 0 <= target_x < ARENA_WIDTH and 0 <= target_y < ARENA_HEIGHT:
                    self.crosshair = Point(target_x, target_y)
                self.dx = 0
                self.dy = 0
        else:
            if self.dx != 0 and self.dy != 0:
                # Diagonal movement attempt: enforce strict corner collision check (supercover raycasting parity).
                # Both orthogonal intermediate steps and the target cell must be walkable to prevent diagonal clipping.
                can_x = self.tilemap.is_walkable(self.player.x + self.dx, self.player.y)
                can_y = self.tilemap.is_walkable(self.player.x, self.player.y + self.dy)
                target = self.tilemap.is_walkable(self.player.x + self.dx, self.player.y + self.dy)

                if can_x and can_y and target:
                    self.player.x += self.dx
                    self.player.y += self.dy
                    self.update_fov()
                self.dx = 0
                self.dy = 0
            elif self.dx != 0 or self.dy != 0:
                target_x = self.player.x + self.dx
                target_y = self.player.y + self.dy
                if self.tilemap.is_walkable(target_x, target_y):
                    self.player.x = target_x
                    self.player.y = target_y
                    self.update_fov()
                self.dx = 0
                self.dy = 0

    def draw(self, screen: Screen) -> None:
        scale_w, scale_h = self.tile_scale
        center_col = screen.size.columns // 2
        center_row = screen.size.rows // 2

        origin_x = center_col - self.player.x * scale_w
        origin_y = center_row - self.player.y * scale_h
        visible = self.visible_cells if self.raytracing_enabled else None
        self.tilemap.draw(screen, origin_x, origin_y, scale=self.tile_scale, visible_cells=visible)

        self.player.draw(screen, origin_x, origin_y, scale=self.tile_scale, transparent_space=True)

        # Render continuous ballistic projectile beam
        if self.shot_ray:
            draw_shot_ray(
                screen,
                self.shot_ray,
                origin_x,
                origin_y,
                scale=self.tile_scale,
                is_opaque=self.tilemap.is_opaque,
            )
        if self.shooting:
            in_fov = self.crosshair in self.visible_cells
            reticle_texture = RETICLE_AMBER_TEXTURE if in_fov else RETICLE_RED_TEXTURE
            reticle_texture.draw(
                screen,
                origin_x,
                origin_y,
                self.crosshair.x,
                self.crosshair.y,
                scale=self.tile_scale,
            )

        # Bottom status bar with scale, vision mode, and preset telemetry
        vision_mode = "Raytracing" if self.raytracing_enabled else "Full Map"
        input_mode = "Shoot" if self.shooting else "Walk"
        trail_mode = "Timed (0.15s)" if self.trail_timed else "Turn"
        scale_label = f"{scale_w}x{scale_h}"
        if self.shooting:
            in_fov = (self.crosshair in self.visible_cells) if self.raytracing_enabled else True
            fire_action = "[LMB/Space/F] Fire" if in_fov else "(Blocked / Out of FOV)"
            aim_hint = f" | aim x: {self.crosshair.x:2d} y: {self.crosshair.y:2d} | {fire_action}"
        else:
            aim_hint = ""
        status_text = f"x: {self.player.x:2d} y: {self.player.y:2d}{aim_hint}"
        controls_text = (
            f"[Tab] Scale: {scale_label} | "
            f"[F1] {vision_mode} | "
            f"[F2] Map: {self.map} | "
            f"[F4] Trail: {trail_mode} | "
            f"[Enter/RMB] {input_mode}"
        )
        screen.draw_text(
            0,
            screen.size.rows - 2,
            status_text.ljust(screen.size.columns)[:screen.size.columns],
            bg_color=Color(48, 48, 48),
        )
        screen.draw_text(
            0,
            screen.size.rows - 1,
            controls_text.ljust(screen.size.columns)[:screen.size.columns],
            bg_color=Color(48, 48, 48),
        )
