from engine.backends import WindowsScreen
from engine.primitives import Symbol, move_cursor
from engine.screen.objects import ScreenObject

from sys import stdout


class Screen:
    """
    A terminal screen abstraction with double buffering.

    The screen maintains two buffers:
    - buffer_old: last rendered state
    - buffer_new: current frame state

    Rendering is performed by diffing these buffers and updating
    only the changed lines in the terminal.

    Coordinates:
        (0, 0) is the top-left corner of the screen.
    """
    EMPTY_SYMBOL = Symbol(" ")

    ALIGNMENTS = {
        "top_left": lambda sw, sh, ow, oh: (0, 0),
        "top": lambda sw, sh, ow, oh: ((sw - ow) // 2, 0),
        "top_right": lambda sw, sh, ow, oh: (sw - ow, 0),
        "left": lambda sw, sh, ow, oh: (0, (sh - oh) // 2),
        "center": lambda sw, sh, ow, oh: ((sw - ow) // 2, (sh - oh) // 2),
        "right": lambda sw, sh, ow, oh: (sw - ow, (sh - oh) // 2),
        "bottom_left": lambda sw, sh, ow, oh: (0, sh - oh),
        "bottom": lambda sw, sh, ow, oh: ((sw - ow) // 2, sh - oh),
        "bottom_right": lambda sw, sh, ow, oh: (sw - ow, sh - oh)
    }

    def __init__(
            self,
            pos: tuple[int, int],
            columns: int,
            lines: int
    ):
        self._screen = WindowsScreen()
        self._screen.enable_ansi()

        self.pos = pos
        self.columns, self.lines = columns, lines

        self.buffer_old = [
            [self.EMPTY_SYMBOL for _ in range(self.columns)]
            for _ in range(self.lines)
        ]

        self.buffer_new = [
            [self.EMPTY_SYMBOL for _ in range(self.columns)]
            for _ in range(self.lines)
        ]
        self.move(pos)
        self.set_size(columns, lines)

    def resize_buffer(self, columns: int, lines: int):
        def resize(buffer):
            buffer_resized = []

            for y in range(lines):
                if y < len(buffer):
                    line = buffer[y][:columns]
                else:
                    line = []
                padding = max(columns - len(line), 0)
                if padding > 0:
                    line.extend(self.EMPTY_SYMBOL for _ in range(padding))
                buffer_resized.append(line)

            return buffer_resized

        self.columns, self.lines = columns, lines
        self.buffer_old = resize(self.buffer_old)
        self.buffer_new = resize(self.buffer_new)

    def set_size(self, columns: int, lines: int):
        self.resize_buffer(columns, lines)
        self._screen.set_buffer_size(columns, lines)
        self._screen.set_window_size(columns, lines)

    def move(self, pos: tuple[int, int]):
        self.pos = pos
        self._screen.set_position_by_chars(pos, self.columns, self.lines)

    def draw(self, screen_object: ScreenObject):
        content = screen_object.content
        for y in range(len(content)):
            screen_y = y + screen_object.pos[1]
            if screen_y < 0:
                continue
            if screen_y >= self.lines:
                break
            line = content[y]
            for x in range(len(line)):
                screen_x = x + screen_object.pos[0]
                if screen_x < 0:
                    continue
                if screen_x >= self.columns:
                    break
                symbol = line[x]
                if symbol == self.EMPTY_SYMBOL:
                    continue
                self.buffer_new[screen_y][screen_x] = symbol

    def place(self, screen_object: ScreenObject, align_by: str):
        alignment = self.ALIGNMENTS.get(align_by)
        if alignment is None:
            raise Exception(f"Unsupported alignment {align_by}")
        pos = alignment(self.columns, self.lines, screen_object.columns, screen_object.lines)
        screen_object.move(pos)

    def update(self):
        """
        Renders only changed lines by comparing buffer_new with buffer_old.
        Updates buffer_old to match the rendered state.
        """
        parts = []
        for y, (line_old, line_new) in enumerate(zip(self.buffer_old, self.buffer_new)):
            if line_old != line_new:
                parts.append(move_cursor(0, y))
                parts.extend(symbol.rendered() for symbol in line_new)
                self.buffer_old[y] = line_new.copy()
        stdout.write("".join(parts))

    def clear(self):
        """
        Clears the current frame buffer (buffer_new).
        Does not immediately update the screen.
        """
        self.buffer_new = [
            [self.EMPTY_SYMBOL for _ in range(self.columns)]
            for _ in range(self.lines)
        ]
