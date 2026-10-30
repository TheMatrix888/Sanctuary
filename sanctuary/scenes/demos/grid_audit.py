"""
Grid alignment and character clipping audit scene.
Fills the entire screen buffer edge-to-edge with '#' glyphs on contrasting backgrounds
to visually verify that character cells are not cropped on the right or bottom edges.
"""
from enum import IntEnum

from sanctuary.core.geometry import Size
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Cell, Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import Commands, Pop, State, ToggleMetrics


class AuditPattern(IntEnum):
    SOLID_CONTRAST = 0
    CHECKERED = 1
    BORDER_HIGHLIGHT = 2


class GridAuditState(State):
    """
    Diagnostic visual scene filling the terminal grid with high-contrast '#' characters.
    Allows auditing Conhost raster alignment, right-edge margins, and bottom-row integrity.
    """
    pattern: AuditPattern
    show_overlay: bool

    def __init__(self, pattern: AuditPattern = AuditPattern.SOLID_CONTRAST) -> None:
        self.pattern = pattern
        self.show_overlay = True

    def handle_input(self, input_handler: InputHandler) -> Commands:
        if input_handler.just_pressed(Key.ESC):
            return Pop()
        if input_handler.just_pressed(Key.TAB):
            # Cycle through audit patterns
            self.pattern = AuditPattern((int(self.pattern) + 1) % len(AuditPattern))
        if input_handler.just_pressed(Key.SPACE):
            self.show_overlay = not self.show_overlay
        if input_handler.just_pressed(Key.F3):
            return ToggleMetrics()
        return None

    def update(self, dt: float, screen_size: Size) -> None:
        pass

    def draw(self, screen: Screen) -> None:
        cols = screen.size.columns
        rows = screen.size.rows

        # 1. Fill entire screen edge-to-edge based on selected pattern
        match self.pattern:
            case AuditPattern.SOLID_CONTRAST:
                # High-contrast crisp white '#' on deep midnight background
                fg = Color(245, 245, 255)
                bg = Color(16, 20, 36)
                fill_cell = Cell("#", fg, bg)
                screen.clear(fill_cell)

            case AuditPattern.CHECKERED:
                # Alternating cell backgrounds to easily inspect individual glyph boundaries
                fg = Color(255, 220, 60)
                bg_even = Color(20, 26, 46)
                bg_odd = Color(38, 48, 80)
                for y in range(rows):
                    for x in range(cols):
                        bg = bg_even if (x + y) % 2 == 0 else bg_odd
                        screen.back_buffer.set_cell(x, y, Cell("#", fg, bg))

            case AuditPattern.BORDER_HIGHLIGHT:
                # Perimeter border highlighted in bright neon red; interior in dim steel blue
                border_fg = Color(255, 75, 75)
                border_bg = Color(60, 15, 20)
                inner_fg = Color(90, 105, 130)
                inner_bg = Color(14, 18, 28)
                for y in range(rows):
                    is_border_y = (y == 0 or y == rows - 1)
                    for x in range(cols):
                        is_border_x = (x == 0 or x == cols - 1)
                        if is_border_x or is_border_y:
                            cell = Cell("#", border_fg, border_bg)
                        else:
                            cell = Cell("#", inner_fg, inner_bg)
                        screen.back_buffer.set_cell(x, y, cell)

        # 2. Optional status overlay on bottom row (toggleable via 'H' for 100% unadulterated edge view)
        if self.show_overlay and rows > 1:
            pattern_names = {
                AuditPattern.SOLID_CONTRAST: "Solid Contrast",
                AuditPattern.CHECKERED: "Checkered Grid",
                AuditPattern.BORDER_HIGHLIGHT: "Perimeter Highlight",
            }
            mode_label = pattern_names[self.pattern]
            overlay_text = (
                f" GRID AUDIT | Size: {cols}x{rows} "
                f"| Pattern: {mode_label} [Tab] "
                f"| Hide HUD [Space] | Telemetry [F3] | Exit [Esc] "
            )
            padded = overlay_text.ljust(cols)[:cols]
            screen.draw_text(
                x=0,
                y=rows - 1,
                text=padded,
                fg_color=Color(240, 240, 240),
                bg_color=Color(40, 44, 60),
            )
