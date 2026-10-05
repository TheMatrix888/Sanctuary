"""
Parametric configuration models and curated presets for procedural snowfall.
"""
from dataclasses import dataclass
from math import sin
from typing import Callable

from sanctuary.core.primitives import Color


@dataclass(slots=True, frozen=True)
class SnowflakeType:
    """
    Strongly typed particle archetype defining visuals, kinematics, and selection weight.
    """
    name: str
    glyphs: tuple[str, ...]
    speed_min: float
    speed_max: float
    color: Color
    wind_factor: float
    chance_weight: int


@dataclass(slots=True, frozen=True)
class SnowfallConfig:
    """
    Immutable scene configuration template for snowfall simulation.
    """
    name: str
    max_snowflakes: int
    wind_func: Callable[[float], float]
    flake_types: tuple[SnowflakeType, ...]
    sway_factor: float = 1.0


def universal_sway(time_sec: float, sway_offset: float, sway_factor: float = 1.0) -> float:
    """
    Universal atmospheric aerodynamic flutter shared across particles.
    """
    return sin(time_sec * 2.2 + sway_offset) * (1.8 * sway_factor)


# =============================================================================
# PRESET 1: Gentle Drift
# =============================================================================

def _calm_wind(t: float) -> float:
    return (sin(t * 0.2) * 0.8) * 3.0


CALM_DRIFT_CONFIG = SnowfallConfig(
    name="Calm Drift",
    max_snowflakes=80,
    wind_func=_calm_wind,
    sway_factor=0.8,
    flake_types=(
        SnowflakeType(
            name="distant",
            glyphs=(".", "·"),
            speed_min=2.0,
            speed_max=4.0,
            color=Color(60, 80, 105),
            wind_factor=0.3,
            chance_weight=7,
        ),
        SnowflakeType(
            name="midground",
            glyphs=("*", "+", "·"),
            speed_min=4.5,
            speed_max=7.5,
            color=Color(150, 180, 210),
            wind_factor=0.6,
            chance_weight=8,
        ),
        SnowflakeType(
            name="foreground",
            glyphs=("*", "o"),
            speed_min=8.0,
            speed_max=12.0,
            color=Color(240, 248, 255),
            wind_factor=1.0,
            chance_weight=4,
        ),
    ),
)


# =============================================================================
# PRESET 2: Blizzard
# =============================================================================

def _blizzard_wind(t: float) -> float:
    return (sin(t * 0.35) * 0.7 + sin(t * 0.9) * 0.3) * 22.0


BLIZZARD_CONFIG = SnowfallConfig(
    name="Blizzard",
    max_snowflakes=140,
    wind_func=_blizzard_wind,
    sway_factor=1.4,
    flake_types=(
        SnowflakeType(
            name="distant",
            glyphs=(".", "·"),
            speed_min=3.0,
            speed_max=6.0,
            color=Color(75, 95, 120),
            wind_factor=0.5,
            chance_weight=8,
        ),
        SnowflakeType(
            name="midground",
            glyphs=("*", "+", "·"),
            speed_min=6.5,
            speed_max=11.0,
            color=Color(165, 195, 225),
            wind_factor=0.85,
            chance_weight=10,
        ),
        SnowflakeType(
            name="foreground",
            glyphs=("*", "o", "O"),
            speed_min=11.5,
            speed_max=18.0,
            color=Color(250, 252, 255),
            wind_factor=1.15,
            chance_weight=5,
        ),
    ),
)


# =============================================================================
# PRESET 3: Squall / Whirlwind
# =============================================================================

def _squall_wind(t: float) -> float:
    return (sin(t * 1.5) * 0.6 + sin(t * 3.2) * 0.4) * 16.0


SQUALL_CONFIG = SnowfallConfig(
    name="Squall Whirlwind",
    max_snowflakes=110,
    wind_func=_squall_wind,
    sway_factor=1.8,
    flake_types=(
        SnowflakeType(
            name="distant",
            glyphs=(".", "·"),
            speed_min=2.5,
            speed_max=5.0,
            color=Color(70, 90, 115),
            wind_factor=0.4,
            chance_weight=7,
        ),
        SnowflakeType(
            name="midground",
            glyphs=("*", "+"),
            speed_min=5.5,
            speed_max=9.5,
            color=Color(160, 190, 220),
            wind_factor=0.8,
            chance_weight=9,
        ),
        SnowflakeType(
            name="foreground",
            glyphs=("*", "o"),
            speed_min=10.0,
            speed_max=15.0,
            color=Color(245, 250, 255),
            wind_factor=1.1,
            chance_weight=4,
        ),
    ),
)


# =============================================================================
# PRESET 4: Petersburg Sleet (Питерский снегопад)
# =============================================================================

def _petersburg_wind(t: float) -> float:
    return (sin(t * 0.4) * 0.7 + sin(t * 1.1) * 0.3) * 14.0


PETERSBURG_SLEET_CONFIG = SnowfallConfig(
    name="Petersburg Sleet",
    max_snowflakes=110,
    wind_func=_petersburg_wind,
    sway_factor=0.9,
    flake_types=(
        SnowflakeType(
            name="raindrop",
            glyphs=("|", "'", "·"),
            speed_min=40.0,
            speed_max=64.0,
            color=Color(55, 140, 245),
            wind_factor=0.06,
            chance_weight=18,
        ),
        SnowflakeType(
            name="distant",
            glyphs=(".", "·"),
            speed_min=2.5,
            speed_max=5.5,
            color=Color(75, 100, 130),
            wind_factor=0.35,
            chance_weight=6,
        ),
        SnowflakeType(
            name="slush_mid",
            glyphs=("*", "+", "·"),
            speed_min=5.5,
            speed_max=9.5,
            color=Color(170, 195, 220),
            wind_factor=0.7,
            chance_weight=8,
        ),
        SnowflakeType(
            name="slush_fg",
            glyphs=("*", "o"),
            speed_min=10.0,
            speed_max=15.0,
            color=Color(230, 240, 250),
            wind_factor=1.05,
            chance_weight=4,
        ),
    ),
)


# =============================================================================
# PRESET 5: Original Draft
# =============================================================================

def _draft_wind(t: float) -> float:
    return (sin(t * 0.35) * 0.65 + sin(t * 0.9) * 0.25) * 18.0


ORIGINAL_DRAFT_CONFIG = SnowfallConfig(
    name="Original Draft",
    max_snowflakes=85,
    wind_func=_draft_wind,
    sway_factor=1.0,
    flake_types=(
        SnowflakeType(
            name="distant",
            glyphs=(".", "·"),
            speed_min=7.2,
            speed_max=18.0,
            color=Color(70, 88, 110),
            wind_factor=0.35,
            chance_weight=35,
        ),
        SnowflakeType(
            name="midground",
            glyphs=("*", "+", "·"),
            speed_min=22.8,
            speed_max=42.0,
            color=Color(160, 185, 215),
            wind_factor=0.70,
            chance_weight=45,
        ),
        SnowflakeType(
            name="foreground",
            glyphs=("*", "o"),
            speed_min=45.0,
            speed_max=75.0,
            color=Color(245, 250, 255),
            wind_factor=1.00,
            chance_weight=20,
        ),
    ),
)

ALL_SNOWFALL_PRESETS: tuple[SnowfallConfig, ...] = (
    CALM_DRIFT_CONFIG,
    BLIZZARD_CONFIG,
    SQUALL_CONFIG,
    PETERSBURG_SLEET_CONFIG,
    ORIGINAL_DRAFT_CONFIG,
)
