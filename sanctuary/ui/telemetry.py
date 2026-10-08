"""
Performance telemetry and HUD overlay widgets for Sanctuary.
Provides sub-cell resolution progress bars and real-time frame workload panels.
"""
from sanctuary.core.clock import FrameMetrics
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen

# Sub-cell fill progression glyphs (from 0/8 empty to 8/8 full cell width)
SUBCELL_BLOCKS = " ▏▎▍▌▋▊▉█"


def render_subcell_bar(chars: int, ratio: float) -> str:
    """
    Renders a horizontal progress bar with 1/8th sub-cell granularity.
    """
    clamped = max(0.0, min(1.0, ratio))
    total_fraction = clamped * chars
    filled_chars = int(total_fraction)
    if filled_chars >= chars:
        return SUBCELL_BLOCKS[-1] * chars
    sub_idx = min(8, max(0, int((total_fraction % 1) / 0.125)))
    result = (SUBCELL_BLOCKS[-1] * filled_chars) + SUBCELL_BLOCKS[sub_idx]
    return result.ljust(chars)


def draw_telemetry_hud(screen: Screen, metrics: FrameMetrics) -> None:
    """
    Renders a minimalist vertical telemetry panel in the bottom-left viewport corner.
    """
    load_ratio = max(0.0, min(1.0, metrics.load_percent / 100.0))
    panel_lines = [
        f" FPS    {metrics.fps:5.1f} ",
        f" Load   [{render_subcell_bar(5, load_ratio)}] {int(metrics.load_percent):3d}% ",
        f" Logic  {metrics.logic_ms:5.1f} ms ",
        f" Render {metrics.render_ms:5.1f} ms ",
    ]

    max_len = max(len(line) for line in panel_lines)
    y_start = max(0, screen.size.rows - len(panel_lines) - 1)
    fg = Color(225, 230, 245)
    bg = Color(18, 20, 28)

    for offset, line in enumerate(panel_lines):
        padded_line = line.ljust(max_len)
        screen.draw_text(0, y_start + offset, padded_line, fg_color=fg, bg_color=bg)
