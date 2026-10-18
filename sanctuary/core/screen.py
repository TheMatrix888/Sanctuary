"""
Screen buffer abstraction for Sanctuary.
Manages double-buffering, differential delta rendering, and hardware flush.
"""
from __future__ import annotations

from dataclasses import dataclass
import time

import sanctuary.core.ansi as ansi
from sanctuary.core.geometry import Size
from sanctuary.core.primitives import Surface, Color, Cell, DEFAULT_FG, DEFAULT_BG
from sanctuary.core.terminal import Terminal


@dataclass(slots=True, frozen=True)
class BufferMetrics:
    avg_bytes: int
    max_bytes: int
    load_percent: float
    overflow_count: int


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
    max_frame_bytes: int | None
    buffer_metrics: BufferMetrics
    _interval_bytes: int
    _interval_overflows: int
    _interval_frames: int
    _last_metrics_time: float

    def __init__(self, terminal: Terminal, max_frame_bytes: int | None = 8192) -> None:
        self.terminal = terminal
        self.max_frame_bytes = max_frame_bytes
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
        self.buffer_metrics = BufferMetrics(
            avg_bytes=0,
            max_bytes=self.max_frame_bytes or 0,
            load_percent=0.0,
            overflow_count=0,
        )
        self._interval_bytes = 0
        self._interval_overflows = 0
        self._interval_frames = 0
        self._last_metrics_time = time.perf_counter()
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
        updates the front buffer, and stages the payload for hardware flush.
        Limits frame output payload to `max_frame_bytes` if configured, deferring remaining dirty cells
        to subsequent frames to prevent terminal buffer overflows.
        """
        buffer = ""
        budget_exhausted = False
        for y in range(self.size.rows):
            old_line = self.front_buffer.cells[y]
            new_line = self.back_buffer.cells[y]
            if old_line != new_line:
                for x in range(self.size.columns):
                    old_cell = old_line[x]
                    new_cell = new_line[x]
                    if old_cell != new_cell:
                        chunk = ""
                        next_last_x, next_last_y = self.last_x, self.last_y
                        if self.last_y != y or self.last_x != x - 1:
                            chunk += ansi.move_cursor(x, y)
                            next_last_x, next_last_y = x, y
                        else:
                            next_last_x = x

                        next_last_fg = self.last_fg
                        if self.last_fg != new_cell.fg_color:
                            chunk += ansi.fg_color(new_cell.fg_color)
                            next_last_fg = new_cell.fg_color

                        next_last_bg = self.last_bg
                        if self.last_bg != new_cell.bg_color:
                            chunk += ansi.bg_color(new_cell.bg_color)
                            next_last_bg = new_cell.bg_color

                        chunk += new_cell.char

                        if self.max_frame_bytes and buffer and (len(buffer) + len(chunk) > self.max_frame_bytes):
                            budget_exhausted = True
                            break

                        self.last_x, self.last_y = next_last_x, next_last_y
                        self.last_fg, self.last_bg = next_last_fg, next_last_bg
                        buffer += chunk
                        self.front_buffer.set_cell(x, y, new_cell)

            if budget_exhausted:
                break

        self._pending_buffer = buffer

        # Record buffer saturation and payload telemetry
        self._interval_bytes += len(buffer)
        if budget_exhausted:
            self._interval_overflows += 1
        self._interval_frames += 1

        now = time.perf_counter()
        if now - self._last_metrics_time >= 1.0:
            avg_b = int(self._interval_bytes / self._interval_frames) if self._interval_frames > 0 else 0
            limit_b = self.max_frame_bytes or 8192
            pct = min(100.0, (avg_b / limit_b * 100.0)) if limit_b > 0 else 0.0
            self.buffer_metrics = BufferMetrics(
                avg_bytes=avg_b,
                max_bytes=limit_b,
                load_percent=pct,
                overflow_count=self._interval_overflows,
            )
            self._interval_bytes = 0
            self._interval_overflows = 0
            self._interval_frames = 0
            self._last_metrics_time = now

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
