"""
Core Engine Configuration — Single Source of Truth for terminal geometry,
typography, rendering buffers, and window lifecycle.
"""
from dataclasses import dataclass

MIN_COLUMNS: int = 60
MIN_ROWS: int = 30


@dataclass(slots=True, frozen=True)
class DisplayConfig:
    """Target hardware display, typography, and canvas buffer parameters."""
    columns: int = 140
    rows: int = 40
    min_columns: int = MIN_COLUMNS
    min_rows: int = MIN_ROWS
    font_name: str = "Cascadia Mono"
    font_size_height: int = 24
    title: str = "Sanctuary [Shiro]"
    icon_path: str = "resources/icons/shiro.ico"
    max_frame_bytes: int = 8192


DEFAULT_DISPLAY_CONFIG = DisplayConfig()
