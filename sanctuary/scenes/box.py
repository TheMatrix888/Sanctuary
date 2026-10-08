"""
Bouncing box demonstration scene with keyboard color inversion.
"""
import random

from sanctuary.core.geometry import Size
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Color, Surface, DEFAULT_BG
from sanctuary.core.screen import Screen
from sanctuary.core.state import State, Command, Pop, ToggleMetrics

BOX_ART = """
+---------------+
|  PRESS SPACE  |
+---------------+
"""

BOX_BASE_COLOR = Color(130, 215, 240)


class BouncingBoxState(State):
    """
    Demonstration state simulating a bouncing box container.
    Supports inverting foreground and background colors on pressing Space.
    """
    sprite: Surface
    velocity_x: float
    velocity_y: float
    base_color: Color
    x: float
    y: float
    speed_x_sign: float
    speed_y_sign: float
    is_inverted: bool
    _initialized: bool

    def __init__(self, velocity_x: float = 38.0, velocity_y: float = 19.0) -> None:
        self.sprite = Surface(BOX_ART)
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.base_color = BOX_BASE_COLOR
        self.reset()

    def reset(self) -> None:
        """Resets dynamic motion coordinates and appearance state to defaults."""
        self.x = 0.0
        self.y = 0.0
        self.speed_x_sign = 1.0
        self.speed_y_sign = 1.0
        self.is_inverted = False
        self._initialized = False

    def on_enter(self) -> None:
        self.reset()

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        if input_handler.just_pressed(Key.ESC):
            return Pop()
        if input_handler.just_pressed(Key.SPACE):
            self.is_inverted = not self.is_inverted
        if input_handler.just_pressed(Key.F3):
            return ToggleMetrics()
        return None

    def update(self, dt: float, screen_size: Size) -> None:
        max_x = max(float(screen_size.columns - self.sprite.size.columns), 1.0)
        max_y = max(float(screen_size.rows - self.sprite.size.rows - 1), 1.0)

        if not self._initialized:
            self.x = random.uniform(0.0, max_x)
            self.y = random.uniform(0.0, max_y)
            self.speed_x_sign = random.choice([-1.0, 1.0])
            self.speed_y_sign = random.choice([-1.0, 1.0])
            self._initialized = True
        else:
            self.x = max(0.0, min(self.x, max_x))
            self.y = max(0.0, min(self.y, max_y))

        self.x += self.velocity_x * self.speed_x_sign * dt
        self.y += self.velocity_y * self.speed_y_sign * dt

        if self.x >= max_x and self.speed_x_sign > 0:
            self.x = max_x
            self.speed_x_sign = -1.0
        elif self.x <= 0.0 and self.speed_x_sign < 0:
            self.x = 0.0
            self.speed_x_sign = 1.0

        if self.y >= max_y and self.speed_y_sign > 0:
            self.y = max_y
            self.speed_y_sign = -1.0
        elif self.y <= 0.0 and self.speed_y_sign < 0:
            self.y = 0.0
            self.speed_y_sign = 1.0

    def draw(self, screen: Screen) -> None:
        if self.is_inverted:
            self.sprite.apply_color(fg_color=DEFAULT_BG, bg_color=self.base_color)
        else:
            self.sprite.apply_color(fg_color=self.base_color, bg_color=DEFAULT_BG)

        screen.draw_surface(int(self.x), int(self.y), self.sprite)

        status_y = screen.size.rows - 1
        invert_mode_label = "[INVERTED]" if self.is_inverted else "[NORMAL]"
        status_text = (
            f" Bouncing Box | Pos: ({int(self.x):2d}, {int(self.y):2d}) "
            f"| Mode: {invert_mode_label} [Space toggle] "
            f"| [F3 Telemetry] | [Esc Back]"
        )
        padded = status_text.ljust(screen.size.columns)[:screen.size.columns]
        screen.draw_text(
            x=0,
            y=status_y,
            text=padded,
            fg_color=Color(200, 200, 220),
            bg_color=Color(24, 24, 32),
        )
