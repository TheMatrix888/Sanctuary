"""
Screen buffer abstraction for Sanctuary.
Manages double-buffering, differential delta rendering, and hardware flush.
"""
from __future__ import annotations

import sanctuary.core.ansi as ansi
from sanctuary.core.geometry import Rect, Size
from sanctuary.core.primitives import Surface, Color, Cell, DEFAULT_FG, DEFAULT_BG
from sanctuary.core.config import DEFAULT_DISPLAY_CONFIG, DisplayConfig
from sanctuary.core.terminal import Terminal


class Screen:
    terminal: Terminal
    config: DisplayConfig
    size: Size
    font_size: Size
    back_buffer: Surface
    front_buffer: Surface
    last_x: int
    last_y: int
    last_fg: Color | None
    last_bg: Color | None
    _pending_chunks: list[str]
    max_frame_bytes: int | None
    _force_full_redraw: bool
    bg_color: Color

    def __init__(
            self,
            terminal: Terminal,
            config: DisplayConfig = DEFAULT_DISPLAY_CONFIG,
            max_frame_bytes: int | None = None,
    ) -> None:
        self.terminal = terminal
        self.config = config
        self.max_frame_bytes = max_frame_bytes or config.max_frame_bytes
        self.bg_color = DEFAULT_BG
        self.apply_config(config)
        self.reset()

    def apply_config(self, config: DisplayConfig) -> None:
        """Cascades display configuration down to the hardware terminal driver."""
        self.config = config
        self.max_frame_bytes = config.max_frame_bytes
        if hasattr(self.terminal, "set_title"):
            self.terminal.set_title(config.title)
        if hasattr(self.terminal, "set_font"):
            self.terminal.set_font(font_name=config.font_name, font_size_height=config.font_size_height)
        if hasattr(self.terminal, "set_size"):
            self.terminal.set_size(columns=config.columns, rows=config.rows)
        if hasattr(self.terminal, "set_icon"):
            self.terminal.set_icon(config.icon_path)

    def reset(self, new_size: Size | None = None, bg_color: Color | None = None) -> None:
        """Initializes or resets double buffers and cursor state."""
        target_bg = bg_color or getattr(self, "bg_color", DEFAULT_BG)
        self.bg_color = target_bg
        self.size = new_size or self.terminal.get_size()
        self.font_size = self.terminal.get_font_size()
        self.back_buffer = Surface.empty(self.size)
        self.front_buffer = Surface.empty(self.size)
        for row in self.front_buffer.cells:
            for i in range(len(row)):
                row[i] = Cell(char="", fg_color=None, bg_color=None)
        self.last_x, self.last_y = -2, -2
        self.last_fg = None
        self.last_bg = target_bg
        self._pending_chunks = []
        self._force_full_redraw = True
        self.terminal.hide_cursor()
        self.terminal.reset(bg_color=target_bg)

    def clear(self, fill_cell: Cell = Cell(" ")) -> None:
        """Clears the back buffer canvas for a new frame."""
        self.bg_color = fill_cell.bg_color
        self.back_buffer.clear(fill_cell)

    def draw_text(
            self,
            x: int,
            y: int,
            text: str,
            fg_color: Color | None = None,
            bg_color: Color | None = None,
    ) -> None:
        if y < 0 or y >= self.size.rows:
            return

        fg_color = fg_color or DEFAULT_FG
        bg_color = bg_color or DEFAULT_BG

        for text_x, char in enumerate(text):
            screen_x = text_x + x
            self.back_buffer.set_cell(
                screen_x,
                y,
                Cell(char, fg_color, bg_color),
            )

    def fill_rect(
        self,
        rect: Rect,
        char: str = " ",
        fg_color: Color | None = None,
        bg_color: Color | None = None,
    ) -> None:
        """Fills a rectangular region on the back buffer canvas with safe boundary clipping."""
        fg_color = fg_color or DEFAULT_FG
        bg_color = bg_color or DEFAULT_BG
        cell = Cell(char, fg_color, bg_color)
        for point in rect:
            if 0 <= point.x < self.size.columns and 0 <= point.y < self.size.rows:
                self.back_buffer.set_cell(point.x, point.y, cell)

    def draw_surface(
        self,
        x: int,
        y: int,
        surface: Surface,
        transparent_space: bool = False,
    ) -> None:
        for surface_y, line in enumerate(surface.cells):
            screen_y = surface_y + y
            if screen_y < 0:
                continue
            if screen_y >= self.size.rows:
                break
            for surface_x, cell in enumerate(line):
                screen_x = surface_x + x
                if screen_x < 0:
                    continue
                if screen_x >= self.size.columns:
                    break
                if transparent_space and cell.char == " ":
                    continue
                self.back_buffer.set_cell(screen_x, screen_y, cell)

    def move_cursor(self, x: int, y: int) -> str:
        self.last_x, self.last_y = x, y
        return ansi.move_cursor(x, y)

    def change_fg(self, color: Color) -> str:
        self.last_fg = color
        return ansi.fg_color(color)

    def change_bg(self, color: Color) -> str:
        self.last_bg = color
        return ansi.bg_color(color)

    def compose(self) -> None:
        """
        Diffs back buffer against front buffer, emits minimal ANSI sequences into memory,
        slices the stream into clean <= 8KB chunks at atomic cell boundaries, updates the front
        buffer, and stages chunks for sequential hardware flush.
        """
        chunks: list[str] = []
        current_chunk = ""
        max_chunk = self.max_frame_bytes or 8192

        if self._force_full_redraw:
            current_chunk += ansi.RESET_ATTRIBUTES + ansi.HIDE_CURSOR
            self.last_fg = None
            self.last_bg = None
            self._force_full_redraw = False

        for y in range(self.size.rows):
            old_line = self.front_buffer.cells[y]
            new_line = self.back_buffer.cells[y]
            if old_line != new_line:
                for x in range(self.size.columns):
                    old_cell = old_line[x]
                    new_cell = new_line[x]
                    if old_cell != new_cell:
                        cell_delta = ""
                        next_last_x, next_last_y = self.last_x, self.last_y
                        if self.last_y != y or self.last_x != x - 1:
                            cell_delta += ansi.move_cursor(x, y)
                            next_last_x, next_last_y = x, y
                        else:
                            next_last_x = x

                        next_last_fg = self.last_fg
                        if self.last_fg != new_cell.fg_color:
                            cell_delta += ansi.fg_color(new_cell.fg_color)
                            next_last_fg = new_cell.fg_color

                        next_last_bg = self.last_bg
                        if self.last_bg != new_cell.bg_color:
                            cell_delta += ansi.bg_color(new_cell.bg_color)
                            next_last_bg = new_cell.bg_color

                        cell_delta += new_cell.char

                        # If adding this cell would exceed the chunk size, seal the current chunk
                        if current_chunk and (len(current_chunk) + len(cell_delta) > max_chunk):
                            chunks.append(current_chunk)
                            current_chunk = ""

                        # If starting a fresh chunk, guarantee explicit cursor positioning
                        if not current_chunk and (self.last_y == y and self.last_x == x - 1):
                            cell_delta = ansi.move_cursor(x, y) + cell_delta
                            next_last_x, next_last_y = x, y

                        self.last_x, self.last_y = next_last_x, next_last_y
                        self.last_fg, self.last_bg = next_last_fg, next_last_bg
                        current_chunk += cell_delta
                        self.front_buffer.set_cell(x, y, new_cell)

        if current_chunk:
            chunks.append(current_chunk)

        self._pending_chunks = chunks

    def flush(self) -> None:
        """
        Flushes all staged ANSI chunks to the physical hardware terminal in <= 8KB packets.
        """
        for chunk in self._pending_chunks:
            self.terminal.write(chunk)
        self._pending_chunks.clear()

    def update(self) -> None:
        """Composes and flushes the frame."""
        self.compose()
        self.flush()

    def check_resize(self) -> bool:
        """
        Detects whether terminal grid dimensions or character font size changed,
        or if a transition between windowed and fullscreen/maximized occurred,
        or if the window was restored from taskbar minimization.
        Triggers immediate buffer reallocation and terminal state synchronization.
        In fullscreen or maximized mode, font changes dynamically fit the grid to screen,
        enabling true optical semantic zoom.
        """
        transition = self.terminal.check_fullscreen_transition()
        restored = self.terminal.check_restore_transition()

        new_font_size = self.terminal.get_font_size()
        font_changed = (new_font_size != self.font_size)

        if font_changed and self.terminal.is_fullscreen_or_maximized():
            self.terminal.fit_to_screen()

        grid_adjusted = self.terminal.check_grid_alignment()

        new_size = self.terminal.get_size()
        if new_size != self.size or font_changed or transition or grid_adjusted:
            self.resize(new_size)
            return True
        elif restored:
            self._force_full_redraw = True
            return True
        return False

    def resize(self, new_size: Size, bg_color: Color | None = None) -> None:
        """Reallocates back and front buffers to match new terminal dimensions and clears hardware terminal."""
        self.reset(new_size, bg_color=bg_color)
