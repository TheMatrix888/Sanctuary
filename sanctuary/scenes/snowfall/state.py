"""
Atmospheric procedural snowfall state implementation.
"""
import random
from dataclasses import dataclass
from math import pi
from sanctuary.core.geometry import Size
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import State, Command, Pop
from sanctuary.scenes.snowfall.config import (
    SnowfallConfig,
    SnowflakeType,
    CALM_DRIFT_CONFIG,
    ALL_SNOWFALL_PRESETS,
    universal_sway,
)


@dataclass(slots=True)
class Snowflake:
    """Represents an active falling snowflake particle."""
    x: float
    y: float
    y_speed: float
    wind_factor: float
    sway_offset: float
    glyph: str
    color: Color


class SnowfallState(State):
    """
    Atmospheric procedural snowfall demonstration scene.
    Supports interactive particle scaling, wind modulation, runtime preset cycling,
    and automatic particle recreation on entry.
    """
    config: SnowfallConfig
    target_count: int
    wind: float
    wind_multiplier: float
    is_paused: bool
    time_seconds: float
    fps: float
    preset_index: int
    flakes: list[Snowflake]

    def __init__(self, config: SnowfallConfig = CALM_DRIFT_CONFIG) -> None:
        self.config = config
        self.target_count = config.max_snowflakes
        self.wind = 0.0
        self.wind_multiplier = 1.0
        self.is_paused = False
        self.time_seconds = 0.0
        self.fps = 60.0

        if config in ALL_SNOWFALL_PRESETS:
            self.preset_index = ALL_SNOWFALL_PRESETS.index(config)
        else:
            self.preset_index = 0

        self.flakes: list[Snowflake] = []

    def reset(self) -> None:
        """Resets particle arrays, simulation clock, and playback multipliers to defaults."""
        self.flakes.clear()
        self.time_seconds = 0.0
        self.target_count = self.config.max_snowflakes
        self.wind_multiplier = 1.0
        self.is_paused = False

    def on_enter(self) -> None:
        """Lifecycle hook: resets and recreates all particles on entering the scene."""
        self.reset()

    def _spawn_flake(self, screen_size: Size, spawn_anywhere: bool) -> Snowflake:
        weights = [flake_type.chance_weight for flake_type in self.config.flake_types]
        chosen_type: SnowflakeType = random.choices(self.config.flake_types, weights=weights, k=1)[0]

        max_x = max(float(screen_size.columns - 1), 1.0)
        max_y = max(float(screen_size.rows - 2), 1.0)

        spawn_y = random.uniform(0.0, max_y) if spawn_anywhere else 0.0

        return Snowflake(
            x=random.uniform(0.0, max_x),
            y=spawn_y,
            y_speed=random.uniform(chosen_type.speed_min, chosen_type.speed_max),
            wind_factor=chosen_type.wind_factor,
            sway_offset=random.uniform(0.0, 2 * pi),
            glyph=random.choice(chosen_type.glyphs),
            color=chosen_type.color,
        )

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        if input_handler.just_pressed(Key.ESC):
            return Pop()

        if input_handler.just_pressed(Key.SPACE):
            self.is_paused = not self.is_paused

        # Adjust flake count
        if input_handler.just_pressed(Key.UP) or input_handler.just_pressed(Key.BRACKET_RIGHT):
            self.target_count = min(self.target_count + 15, 350)
        elif input_handler.just_pressed(Key.DOWN) or input_handler.just_pressed(Key.BRACKET_LEFT):
            self.target_count = max(self.target_count - 15, 10)

        # Modulate wind force (bounded to >= 0.0 as oscillation functions are naturally bidirectional)
        if input_handler.just_pressed(Key.RIGHT):
            self.wind_multiplier = round(min(self.wind_multiplier + 0.2, 3.0), 2)
        elif input_handler.just_pressed(Key.LEFT):
            self.wind_multiplier = round(max(self.wind_multiplier - 0.2, 0.0), 2)

        # Cycle preset on Tab
        if input_handler.just_pressed(Key.TAB):
            self.preset_index = (self.preset_index + 1) % len(ALL_SNOWFALL_PRESETS)
            self.config = ALL_SNOWFALL_PRESETS[self.preset_index]
            self.reset()

        return None

    def update(self, dt: float, screen_size: Size) -> None:
        if dt > 0.0:
            instant_fps = 1.0 / dt
            self.fps = self.fps * 0.9 + instant_fps * 0.1

        if self.is_paused:
            return

        self.time_seconds += dt

        # Spawn missing flakes up to target count
        while len(self.flakes) < self.target_count:
            self.flakes.append(self._spawn_flake(screen_size, spawn_anywhere=True))

        # Trim surplus flakes if count was reduced
        if len(self.flakes) > self.target_count:
            del self.flakes[self.target_count:]

        self.wind = self.config.wind_func(self.time_seconds) * self.wind_multiplier
        max_y = float(screen_size.rows - 2)
        cols = max(float(screen_size.columns), 1.0)

        for i, flake in enumerate(self.flakes):
            sway = universal_sway(self.time_seconds, flake.sway_offset, self.config.sway_factor) * min(flake.wind_factor * 1.5, 1.0)
            flake.x = (flake.x + (self.wind * flake.wind_factor + sway) * dt) % cols
            flake.y += flake.y_speed * dt

            # Recycle flake when hitting bottom boundary
            if flake.y > max_y:
                self.flakes[i] = self._spawn_flake(screen_size, spawn_anywhere=False)

    def draw(self, screen: Screen) -> None:
        cols = screen.size.columns
        max_y = screen.size.rows - 2

        for flake in self.flakes:
            int_x = int(flake.x)
            int_y = int(flake.y)
            if 0 <= int_y <= max_y and 0 <= int_x < cols:
                screen.draw_text(int_x, int_y, flake.glyph, flake.color)

        # Status bar telemetry
        status_y = screen.size.rows - 1
        pause_label = " [PAUSED]" if self.is_paused else ""
        status_text = (
            f" Snowfall: {self.config.name}{pause_label} "
            f"| Flakes: {len(self.flakes)} [↑/↓] "
            f"| Wind: {self.wind_multiplier:.1f}x [←/→] "
            f"| Dir: {self.wind:.1f} {"←" if self.wind < 0 else "→"} "
            f"| FPS: {self.fps:2.0f} "
            f"| [Tab Preset] [Space] [Esc Back]"
        )
        padded = status_text.ljust(cols)[:cols]
        screen.draw_text(
            x=0,
            y=status_y,
            text=padded,
            fg_color=Color(200, 215, 235),
            bg_color=Color(18, 24, 34),
        )
