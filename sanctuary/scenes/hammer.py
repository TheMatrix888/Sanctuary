"""
Bouncing hammer demonstration scene with bounce color cycling and horizontal mirroring.
"""
from sanctuary.core.geometry import Size
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Color, Surface, DEFAULT_BG
from sanctuary.core.screen import Screen
from sanctuary.core.state import State, Command, Pop

HAMMER_ART = """
/-\\
|#|=====
\\_/
"""

HAMMER_PALETTE: list[Color] = [
    Color(0, 230, 230),    # Neon Cyan
    Color(255, 170, 40),   # Warm Amber
    Color(255, 70, 150),   # Hot Pink
    Color(80, 240, 120),   # Mint Green
    Color(170, 130, 255),  # Soft Lavender
    Color(255, 90, 90),    # Coral Red
]


class BouncingHammerState(State):
    """
    Demonstration state simulating a hammer bouncing diagonally across the terminal,
    horizontally mirroring its sprite on direction change and advancing its color from
    a fixed palette on each wall impact.
    """
    sprite_left: Surface
    sprite_right: Surface
    trip_time_seconds: float
    fps: float
    x: float
    y: float
    speed_x_sign: float
    speed_y_sign: float
    color_index: int

    def __init__(self, trip_time_seconds: float = 5.0) -> None:
        self.sprite_left = Surface(HAMMER_ART)
        self.sprite_right = self.sprite_left.flip_x()
        self.trip_time_seconds = trip_time_seconds
        self.fps = 60.0
        self.reset()

    def reset(self) -> None:
        """Resets dynamic motion coordinates and palette cycle to defaults."""
        self.x = 0.0
        self.y = 0.0
        self.speed_x_sign = 1.0
        self.speed_y_sign = 1.0
        self.color_index = 0

    def on_enter(self) -> None:
        self.reset()

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        if input_handler.just_pressed(Key.ESC):
            return Pop()
        return None

    def _on_bounce(self) -> None:
        """Advances to the next color in the palette upon collision with a boundary."""
        self.color_index = (self.color_index + 1) % len(HAMMER_PALETTE)

    def update(self, dt: float, screen_size: Size) -> None:
        if dt > 0.0:
            instant_fps = 1.0 / dt
            self.fps = self.fps * 0.9 + instant_fps * 0.1

        max_x = max(float(screen_size.columns - self.sprite_right.size.columns), 1.0)
        max_y = max(float(screen_size.rows - self.sprite_right.size.rows - 1), 1.0)
        speed_x = (max_x / self.trip_time_seconds) * self.speed_x_sign
        speed_y = (max_y / self.trip_time_seconds) * self.speed_y_sign

        self.x += speed_x * dt
        self.y += speed_y * dt

        bounced = False

        if self.x >= max_x and self.speed_x_sign > 0:
            self.x = max_x
            self.speed_x_sign = -1.0
            bounced = True
        elif self.x <= 0.0 and self.speed_x_sign < 0:
            self.x = 0.0
            self.speed_x_sign = 1.0
            bounced = True

        if self.y >= max_y and self.speed_y_sign > 0:
            self.y = max_y
            self.speed_y_sign = -1.0
            bounced = True
        elif self.y <= 0.0 and self.speed_y_sign < 0:
            self.y = 0.0
            self.speed_y_sign = 1.0
            bounced = True

        if bounced:
            self._on_bounce()

    def draw(self, screen: Screen) -> None:
        active_sprite = self.sprite_right if self.speed_x_sign > 0 else self.sprite_left
        active_color = HAMMER_PALETTE[self.color_index]
        active_sprite.apply_color(fg_color=active_color, bg_color=DEFAULT_BG)

        screen.draw_surface(int(self.x), int(self.y), active_sprite)

        status_y = screen.size.rows - 1
        direction_label = "-->" if self.speed_x_sign > 0 else "<--"
        status_text = (
            f" Bouncing Hammer | Pos: ({int(self.x):2d}, {int(self.y):2d}) {direction_label} "
            f"| Palette: [{self.color_index + 1}/{len(HAMMER_PALETTE)}] "
            f"| FPS: {self.fps:2.0f} "
            f"| [Esc Back]"
        )
        padded = status_text.ljust(screen.size.columns)[:screen.size.columns]
        screen.draw_text(
            x=0,
            y=status_y,
            text=padded,
            fg_color=Color(200, 200, 220),
            bg_color=Color(24, 24, 32),
        )
