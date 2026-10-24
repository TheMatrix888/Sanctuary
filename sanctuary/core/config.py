"""
Core Engine Configuration — Single Source of Truth for terminal geometry,
typography, rendering buffers, and window lifecycle.
"""
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class DisplayConfig:
    """Target hardware display, typography, and canvas buffer parameters."""
    columns: int = 140
    rows: int = 40
    font_name: str = "Cascadia Mono"
    font_size_height: int = 24
    title: str = "Sanctuary [Shiro]"
    icon_path: str = "resources/icons/shiro.ico"
    max_frame_bytes: int = 8192


DEFAULT_DISPLAY_CONFIG = DisplayConfig()
