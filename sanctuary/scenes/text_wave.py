"""
Sanctuary Rainbow TrueColor banner and harmonic text wave demonstration scene.
"""
import colorsys
import math
from math import sin

from sanctuary.core.geometry import Size
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import State, Command, Pop

BANNER_ART = [
    "███████╗ █████╗ ███╗   ██╗ ██████╗████████╗██╗   ██╗ █████╗ ██████╗ ██╗   ██╗",
    "██╔════╝██╔══██╗████╗  ██║██╔════╝╚══██╔══╝██║   ██║██╔══██╗██╔══██╗╚██╗ ██╔╝",
    "███████╗███████║██╔██╗ ██║██║        ██║   ██║   ██║███████║██████╔╝ ╚████╔╝ ",
    "╚════██║██╔══██║██║╚██╗██║██║        ██║   ██║   ██║██╔══██║██╔══██╗  ╚██╔╝  ",
    "███████║██║  ██║██║ ╚████║╚██████╗   ██║   ╚██████╔╝██║  ██║██║  ██║   ██║   ",
    "╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ",
]


class RainbowTextState(State):
    """
    Demonstration state rendering a stylized Sanctuary banner and harmonic text wave demonstration scene
    with continuous TrueColor rainbow spectrum modulation.
    """
    fps: float
    time: float
    wave_angle: float

    ARROWS = ("↑", "↑→", "→", "↓→", "↓", "←↓", "←", "↑←")

    def __init__(self, angle: float = 270.0) -> None:
        self.fps = 60.0
        self.wave_angle = float(angle)
        self.reset()

    def reset(self) -> None:
        """Resets animation timer to initial zero phase."""
        self.time = 0.0
        self.wave_angle = 270.0

    def on_enter(self) -> None:
        self.reset()

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        if input_handler.just_pressed(Key.ESC):
            return Pop()
        if input_handler.just_pressed(Key.RIGHT):
            self.wave_angle = (self.wave_angle + 15.0) % 360.0
        if input_handler.just_pressed(Key.LEFT):
            self.wave_angle = (self.wave_angle - 15.0) % 360.0

        return None

    def update(self, dt: float, screen_size: Size) -> None:
        self.time += dt
        if dt > 0.0:
            instant_fps = 1.0 / dt
            self.fps = self.fps * 0.9 + instant_fps * 0.1

    def draw(self, screen: Screen) -> None:
        cols = screen.size.columns
        rows = screen.size.rows

        # 1. Render multi-line banner centered horizontally
        banner_width = len(BANNER_ART[0]) if BANNER_ART else 0
        start_x = max((cols - banner_width) // 2, 0)
        start_y = max(rows // 4 - 2, 1)

        # Navigational compass heading:
        # 0° = North (Up ↑), 90° = East (Right →), 180° = South (Down ↓), 270° = West (Left ←)
        rad = math.radians(self.wave_angle)
        dir_x = math.sin(rad)
        dir_y = -math.cos(rad)

        for line_idx, line in enumerate(BANNER_ART):
            y = start_y + line_idx
            if y >= rows - 3:
                break
            for char_idx, char in enumerate(line):
                x = start_x + char_idx
                if x >= cols:
                    break
                if char != " ":
                    # 2.0 aspect ratio correction for rectangular terminal character cells
                    proj = char_idx * dir_x + line_idx * 2.0 * dir_y
                    hue = (proj * 0.015 - self.time * 0.35) % 1.0
                    r_norm, g_norm, b_norm = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                    fg = Color(int(r_norm * 255), int(g_norm * 255), int(b_norm * 255))
                    screen.draw_text(x, y, char, fg_color=fg)

        # 2. Render dynamic sine wave text beneath banner
        wave_text = "~ ~ ~  S A N C T U A R Y   T E R M I N A L   E N G I N E  ~ ~ ~"
        wave_start_x = max((cols - len(wave_text)) // 2, 0)
        base_wave_y = start_y + len(BANNER_ART) + 3

        for i, char in enumerate(wave_text):
            x = wave_start_x + i
            if x >= cols:
                break
            y_offset = int(sin(self.time * 3.0 + i * 0.2) * 1.5)
            y = base_wave_y + y_offset
            if 0 <= y < rows - 1:
                hue = (self.time * 0.5 + i * 0.03) % 1.0
                r_norm, g_norm, b_norm = colorsys.hsv_to_rgb(hue, 0.9, 1.0)
                fg = Color(int(r_norm * 255), int(g_norm * 255), int(b_norm * 255))
                screen.draw_text(x, y, char, fg_color=fg)

        # 3. Bottom status telemetry
        arrow_idx = int((self.wave_angle + 22.5) % 360.0 // 45.0)
        arrow = self.ARROWS[arrow_idx]

        status_y = rows - 1
        status_text = (
            f" Rainbow TrueColor Spectrum Wave "
            f"| Angle: {self.wave_angle:3.0f}° {arrow:<2s} [←/→] "
            f"| FPS: {self.fps:2.0f} "
            f"| [Esc Back]"
        )
        padded = status_text.ljust(cols)[:cols]
        screen.draw_text(
            x=0,
            y=status_y,
            text=padded,
            fg_color=Color(200, 200, 220),
            bg_color=Color(24, 24, 32),
        )
