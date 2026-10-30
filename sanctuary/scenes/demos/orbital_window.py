"""
Orbital satellite window demonstration scene.
Shrinks the console down to a compact procedurally generated micro-window,
and propels the physical OS window along a circular orbit around the center of the display monitor
purely using high-level Terminal protocol methods.
"""
import math

import sanctuary.core.ansi as ansi
from sanctuary.core.geometry import Size
from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Cell, Color, Surface
from sanctuary.core.screen import Screen
from sanctuary.core.state import Commands, Pop, State, ToggleMetrics
from sanctuary.core.terminal import Terminal

# =========================================================================
# EXPERIMENTAL DIMENSIONS (Freely tweak these constants to test window limits!)
# =========================================================================
TARGET_COLS: int = 60
TARGET_ROWS: int = 30


def build_orbit_surface(cols: int, rows: int, is_orbiting: bool) -> Surface:
    """
    Procedurally synthesizes a pixel-perfect terminal Surface box of any (cols, rows)
    with centered title, mascot kaomoji (:з), and navigation shortcuts.
    """
    cols = max(4, cols)
    rows = max(2, rows)
    inner_w = max(0, cols - 2)
    inner_h = max(0, rows - 2)

    border_fg = Color(80, 220, 255) if is_orbiting else Color(255, 180, 60)
    bg_color = Color(16, 26, 40) if is_orbiting else Color(40, 28, 16)
    text_fg = Color(220, 240, 255)
    mascot_fg = Color(120, 255, 180) if is_orbiting else Color(255, 210, 100)

    status = "ORBIT" if is_orbiting else "PAUSED"
    if inner_h <= 1:
        lines = [f"{status} :з"]
    elif inner_h == 2:
        lines = [status, ":з [ESC]"]
    elif inner_h == 3:
        lines = [status, ":з", "[ESC]"]
    else:
        lines = [status, ":з", "[SPACE]", "[ESC]"]

    surface = Surface.empty(Size(cols, rows))
    for y in range(rows):
        for x in range(cols):
            if y == 0 and x == 0:
                char = "┌"
            elif y == 0 and x == cols - 1:
                char = "┐"
            elif y == rows - 1 and x == 0:
                char = "└"
            elif y == rows - 1 and x == cols - 1:
                char = "┘"
            elif y == 0 or y == rows - 1:
                char = "─"
            elif x == 0 or x == cols - 1:
                char = "│"
            else:
                char = " "
            surface.cells[y][x] = Cell(char, border_fg, bg_color)

    pad_top = max(0, (inner_h - len(lines)) // 2)
    for line_idx, line_text in enumerate(lines[:inner_h]):
        y_pos = 1 + pad_top + line_idx
        trimmed = line_text[:inner_w]
        x_start = 1 + max(0, (inner_w - len(trimmed)) // 2)
        for char_idx, char in enumerate(trimmed):
            fg = mascot_fg if ":з" in trimmed and char in ":з" else text_fg
            surface.cells[y_pos][x_start + char_idx] = Cell(char, fg, bg_color)

    return surface


class OrbitalWindowState(State):
    """
    Demonstration showcasing platform-agnostic window orbital motion.
    Procedurally adapts to TARGET_COLS x TARGET_ROWS and orbits the window frame
    around the center of the screen via the Terminal protocol.
    """
    is_orbiting: bool
    angle: float
    angular_speed: float
    cols: int
    rows: int
    initial_size: Size | None
    terminal: Terminal | None
    _screen: Screen | None
    surface_active: Surface
    surface_paused: Surface

    def __init__(self, angular_speed: float = 1.0) -> None:
        self.is_orbiting = False
        self.angle = 0.0
        self.angular_speed = angular_speed
        self.cols = TARGET_COLS
        self.rows = TARGET_ROWS
        self.initial_size = None
        self.terminal = None
        self._screen = None

        self._rebuild_surfaces()

    def _rebuild_surfaces(self) -> None:
        """Regenerates the procedural surfaces matching active (cols, rows)."""
        self.surface_active = build_orbit_surface(self.cols, self.rows, is_orbiting=True)
        self.surface_paused = build_orbit_surface(self.cols, self.rows, is_orbiting=False)

    def on_enter(self) -> None:
        """Enforces micro-window geometry on entering or re-entering the state."""
        if self.terminal:
            self.terminal.set_size(self.cols, self.rows, center=True)
            self.terminal.hide_cursor()
            if self._screen:
                self._screen.resize(Size(self.cols, self.rows))

    def handle_input(self, input_handler: InputHandler) -> Commands:
        if input_handler.just_pressed(Key.ESC):
            self._restore_geometry()
            return Pop()

        if input_handler.just_pressed(Key.SPACE, Key.ENTER):
            self.is_orbiting = not self.is_orbiting

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
        # Check if user dynamically modified constants
        if self.cols != TARGET_COLS or self.rows != TARGET_ROWS:
            self.cols = TARGET_COLS
            self.rows = TARGET_ROWS
            self._rebuild_surfaces()
            if self.terminal:
                self.terminal.set_size(self.cols, self.rows, center=True)
            if self._screen:
                self._screen.resize(Size(self.cols, self.rows))

        if not self.terminal:
            return

        if self.is_orbiting:
            self.angle = (self.angle + self.angular_speed * dt) % (2.0 * math.pi)

        # Query display metrics cleanly from Terminal protocol
        screen_w, screen_h = self.terminal.get_monitor_size_pixels()
        win_w, win_h = self.terminal.get_window_size_pixels()

        center_x = screen_w // 2
        center_y = screen_h // 2

        # Calculate circular orbit trajectory (radius derived from display geometry)
        orbit_radius = int(min(screen_w, screen_h) * 0.38)
        pos_x = int(center_x - (win_w // 2) + orbit_radius * math.cos(self.angle))
        pos_y = int(center_y - (win_h // 2) + orbit_radius * math.sin(self.angle))

        # Smoothly reposition window without altering size or focus via Terminal method
        self.terminal.set_position(pos_x, pos_y)

    def draw(self, screen: Screen) -> None:
        self._screen = screen
        if self.terminal is None:
            self.terminal = screen.terminal
            self.initial_size = screen.size
            self.terminal.set_size(self.cols, self.rows, center=True)
            screen.resize(Size(self.cols, self.rows))

        self.terminal.hide_cursor()
        bg_color = Color(10, 14, 20)
        screen.clear(Cell(" ", Color(200, 200, 200), bg_color))

        surface = self.surface_active if self.is_orbiting else self.surface_paused
        # Position surface at (0, 0) since it exactly matches (cols, rows)
        screen.draw_surface(0, 0, surface)
