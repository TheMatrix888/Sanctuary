"""
Standalone visual demonstration and diagnostic scenes for Sanctuary.
Provides bouncing shapes, text wave distortion, grid alignment tests, and window overcoming demos.
"""
from .box import BouncingBoxState
from .grid_audit import GridAuditState
from .hammer import BouncingHammerState
from .orbital_window import OrbitalWindowState
from .overcoming import OvercomingState
from .text_wave import RainbowTextState

__all__ = [
    "BouncingBoxState",
    "GridAuditState",
    "BouncingHammerState",
    "OrbitalWindowState",
    "OvercomingState",
    "RainbowTextState",
]
