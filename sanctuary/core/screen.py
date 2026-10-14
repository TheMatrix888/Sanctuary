"""
Screen buffer abstraction for Sanctuary.
Manages double-buffering, differential delta rendering, and hardware flush.
"""
from __future__ import annotations

import sanctuary.core.ansi as ansi
from sanctuary.core.geometry import Size
from sanctuary.core.primitives import Surface, Color, Cell, DEFAULT_FG, DEFAULT_BG
from sanctuary.core.terminal import Terminal


class Screen:
    terminal: Terminal
    size: Size
    font_size: Size
    back_buffer: Surface
    front_buffer: Surface
    last_x: int
    last_y: int
    last_fg: Color | None
    last_bg: Color | None
    _pending_buffer: str

    def __init__(self, terminal: Terminal) -> None:
        self.terminal = terminal
        self.reset()

    def reset(self, new_size: Size | None = None) -> None:
        """Initializes or resets double buffers and cursor state."""
        self.size = new_size or self.terminal.get_size()
        self.font_size = self.terminal.get_font_size()
        self.back_buffer = Surface.empty(self.size)
        self.front_buffer = Surface.empty(self.size)
        self.last_x, self.last_y = -2, -2
        self.last_fg = None
        self.last_bg = None
        self._pending_buffer = ""
        self.terminal.reset()

    def clear(self, fill_cell: Cell = Cell(" ")) -> None:
        """Clears the back buffer canvas for a new frame."""
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

    def draw_surface(self, x: int, y: int, surface: Surface) -> None:
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
        updates the front buffer, and stages the payload for hardware flush.
        """
        buffer = ""
        for y in range(self.size.rows):
            old_line = self.front_buffer.cells[y]
            new_line = self.back_buffer.cells[y]
            if old_line != new_line:
                for x in range(self.size.columns):
                    old_cell = old_line[x]
                    new_cell = new_line[x]
                    if old_cell != new_cell:
                        if self.last_y != y or self.last_x != x - 1:
                            buffer += self.move_cursor(x, y)
                        else:
                            self.last_x = x

                        if self.last_fg != new_cell.fg_color:
                            buffer += self.change_fg(new_cell.fg_color)
                        if self.last_bg != new_cell.bg_color:
                            buffer += self.change_bg(new_cell.bg_color)

                        buffer += new_cell.char
                        self.front_buffer.set_cell(x, y, new_cell)

        self._pending_buffer = buffer

    def flush(self) -> None:
        """
        Flushes the staged ANSI buffer to the physical hardware terminal.
        """
        if self._pending_buffer:
            self.terminal.write(self._pending_buffer)
            self._pending_buffer = ""

    def update(self) -> None:
        """Composes and flushes the frame."""
        self.compose()
        self.flush()

    def check_resize(self) -> bool:
        """
        Detects whether terminal grid dimensions or character font size changed,
        or if a transition between windowed and fullscreen/maximized occurred.
        Triggers immediate buffer reallocation and terminal state synchronization.
        In fullscreen or maximized mode, font changes dynamically fit the grid to screen,
        enabling true optical semantic zoom.
        """
        transition = self.terminal.check_fullscreen_transition()

        new_font_size = self.terminal.get_font_size()
        font_changed = (new_font_size != self.font_size)

        if font_changed and self.terminal.is_fullscreen_or_maximized():
            self.terminal.fit_to_screen()

        new_size = self.terminal.get_size()
        if new_size != self.size or font_changed or transition:
            self.resize(new_size)
            return True
        return False

    def resize(self, new_size: Size) -> None:
        """Reallocates back and front buffers to match new terminal dimensions."""
        self.reset(new_size)
