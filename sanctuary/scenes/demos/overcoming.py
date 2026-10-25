"""
Window overcoming demonstration scene (измученное превозмогание).
Features a centered toggle button card and 4 corner bracket surfaces that illustrate
window geometry breathing via sinusoidal modulation with desktop display centering.
Applies target background tinting to hardware terminal resets, eliminating black background strobing.
"""
import math
import time

import sanctuary.core.ansi as ansi
from sanctuary.core.geometry import Size
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Cell, Color, Surface
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Pop, State, ToggleMetrics
from sanctuary.core.terminal import Terminal

OVERCOMING_BG = Color(14, 16, 22)

# --- ASCII Art Surfaces ---

CARD_INACTIVE_ART = """
┌────────────────┐
│   OVERCOMING   │
├────────────────┤
│  [ ] RELAXED   │
│                │
│ [Space] Toggle │
└────────────────┘
"""

CARD_ACTIVE_ART = """
┌────────────────┐
│   OVERCOMING   │
├────────────────┤
│ [*] STRUGGLING │
│                │
│ [Space] Toggle │
└────────────────┘
"""

TL_CORNER_ART = """
┌──
│TL
"""

TR_CORNER_ART = """
──┐
TR│
"""

BL_CORNER_ART = """
│BL
└──
"""

BR_CORNER_ART = """
BR│
──┘
"""


class OvercomingState(State):
    """
    Interactive demonstration demonstrating programmatic control over terminal geometry.
    Modulates window size via sinusoidal math while centering the window on the desktop display,
    centering the button card inside the viewport, and anchoring 4 corner surfaces.
    """
    is_active: bool
    initial_size: Size | None
    terminal: Terminal | None
    _screen: Screen | None

    card_inactive: Surface
    card_active: Surface
    corner_tl: Surface
    corner_tr: Surface
    corner_bl: Surface
    corner_br: Surface

    def __init__(self, terminal: Terminal | None = None) -> None:
        self.is_active = False
        self.initial_size = None
        self.terminal = terminal
        self._screen = None

        # Card palettes
        inactive_border = Color(90, 120, 160)
        card_bg = Color(20, 24, 34)
        active_border = Color(255, 205, 60)
        active_bg = Color(28, 36, 30)

        self.card_inactive = Surface(CARD_INACTIVE_ART, inactive_border, card_bg)
        self.card_active = Surface(CARD_ACTIVE_ART, active_border, active_bg)

        # Highlight button lines inside surfaces
        for x in range(1, self.card_inactive.size.columns - 1):
            cell = self.card_inactive.cells[3][x]
            self.card_inactive.cells[3][x] = Cell(cell.char, Color(190, 200, 215), Color(24, 28, 38))
        for x in range(1, self.card_active.size.columns - 1):
            cell = self.card_active.cells[3][x]
            self.card_active.cells[3][x] = Cell(cell.char, Color(30, 255, 140), Color(20, 45, 30))

        # Corner palettes: luminous cyan brackets
        corner_fg = Color(110, 195, 255)
        corner_bg = Color(16, 24, 38)
        self.corner_tl = Surface(TL_CORNER_ART, corner_fg, corner_bg)
        self.corner_tr = Surface(TR_CORNER_ART, corner_fg, corner_bg)
        self.corner_bl = Surface(BL_CORNER_ART, corner_fg, corner_bg)
        self.corner_br = Surface(BR_CORNER_ART, corner_fg, corner_bg)

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        if input_handler.just_pressed(Key.ESC):
            self._restore_geometry()
            return Pop()

        if input_handler.just_pressed(Key.SPACE) or input_handler.just_pressed(Key.ENTER):
            self.is_active = not self.is_active
            if not self.is_active:
                self._restore_geometry()

        if input_handler.just_pressed(Key.F3):
            return ToggleMetrics()

        return None

    def _restore_geometry(self) -> None:
        """Restores original terminal window size, resets ANSI attributes, and forces clean screen clear."""
        if self.terminal and self.initial_size:
            # 1. Reset hardware terminal attributes and active brush to baseline
            self.terminal.write(ansi.RESET_ATTRIBUTES + ansi.bg_color(Color(0, 0, 0)))

            # 2. Restore window geometry and center on desktop
            cur_size = self.terminal.get_size()
            if cur_size.columns != self.initial_size.columns or cur_size.rows != self.initial_size.rows:
                self.terminal.set_size(self.initial_size.columns, self.initial_size.rows, center=True)

            # 3. Cleanly reset and clear screen buffers so returning state (Menu) starts completely spotless
            if self._screen:
                self._screen.reset(self.initial_size)
                self._screen.clear()
                self._screen.compose()
                self._screen.flush()

    def on_exit(self) -> None:
        self._restore_geometry()

    def update(self, dt: float, screen_size: Size) -> None:
        if not self.is_active or not self.terminal:
            return

        now = time.time()
        # Modulate width and height respecting empirical Conhost hardware threshold (ROWS >= 30)
        target_width = int(60 + abs(math.cos(now * 0.5) * 30))
        target_height = int(30 + abs(math.sin(now * 0.5) * 10))

        cur_size = self.terminal.get_size()
        if target_width != cur_size.columns or target_height != cur_size.rows:
            self.terminal.set_size(target_width, target_height, center=True)
            if self._screen:
                self._screen.resize(Size(target_width, target_height), bg_color=OVERCOMING_BG)

    def draw(self, screen: Screen) -> None:
        self._screen = screen
        self.terminal = screen.terminal
        if self.initial_size is None:
            self.initial_size = screen.size

        cols = screen.size.columns
        rows = screen.size.rows

        # Dark sleek canvas
        screen.clear(Cell(" ", Color(200, 200, 200), OVERCOMING_BG))

        # 1. Four corner surfaces anchored to viewport boundaries
        screen.draw_surface(0, 0, self.corner_tl)
        screen.draw_surface(cols - self.corner_tr.size.columns, 0, self.corner_tr)
        screen.draw_surface(0, rows - self.corner_bl.size.rows, self.corner_bl)
        screen.draw_surface(cols - self.corner_br.size.columns, rows - self.corner_br.size.rows, self.corner_br)

        # 2. Central button card surface
        card = self.card_active if self.is_active else self.card_inactive
        x_start = max(0, (cols - card.size.columns) // 2)
        y_start = max(0, (rows - card.size.rows) // 2)
        screen.draw_surface(x_start, y_start, card)

        # Optional dynamic size readout on line 4 of card if viewport allows
        if card.size.rows > 4 and card.size.columns > 4:
            size_str = f"Size: {cols}x{rows}".center(card.size.columns - 2)
            screen.draw_text(
                x_start + 1,
                y_start + 4,
                size_str,
                fg_color=Color(140, 160, 190),
                bg_color=card.cells[4][1].bg_color,
            )
