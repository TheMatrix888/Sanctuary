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
    Renders a minimalist vertical telemetry panel in the top-right viewport corner.
    Positioning at row 0 guarantees immediate rendering during top-to-bottom differential scans,
    preventing HUD freezes during frame buffer saturation.
    """
    load_ratio = metrics.load_percent / 100.0

    panel_items: list[tuple[str, bool]] = [
        (f" FPS   {metrics.fps:5.1f} (max {metrics.max_ms:4.1f}ms) ", False),
        (f" Load  [{render_subcell_bar(5, load_ratio)}] {int(metrics.load_percent):3d}% ", False),
        (f" Logic {metrics.logic_ms:5.1f} ms ", False),
        (f" Draw  {metrics.draw_ms:5.1f} ms ", False),
        (f" Flush {metrics.flush_ms:5.1f} ms ", False),
    ]

    max_len = max(len(text) for text, _ in panel_items)
    x_start = max(0, screen.size.columns - max_len)
    y_start = 0
    fg = Color(225, 230, 245)
    bg = Color(18, 20, 28)
    alert_fg = Color(255, 95, 95)

    for offset, (text, is_alert) in enumerate(panel_items):
        padded_line = text.ljust(max_len)
        item_fg = alert_fg if is_alert else fg
        screen.draw_text(x_start, y_start + offset, padded_line, fg_color=item_fg, bg_color=bg)
