"""
Screen buffer abstraction for Sanctuary.
Manages double-buffering, differential delta rendering, and hardware flush.
"""
from sanctuary.core.primitives import Surface, Color, Cell, DEFAULT_FG, DEFAULT_BG
from sanctuary.core.terminal import Terminal


class Screen:
    def __init__(self, terminal: Terminal) -> None:
        self.terminal = terminal
        self.size = terminal.get_size()
        self.back_buffer = Surface.empty(self.size)
        self.front_buffer = Surface.empty(self.size)
        self.last_x, self.last_y = -2, -2
        self.last_fg: Color | None = None
        self.last_bg: Color | None = None

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
        return f"\033[{y + 1};{x + 1}H"

    def change_fg(self, color: Color) -> str:
        self.last_fg = color
        r, g, b = color
        return f"\033[38;2;{r};{g};{b}m"

    def change_bg(self, color: Color) -> str:
        self.last_bg = color
        r, g, b = color
        return f"\033[48;2;{r};{g};{b}m"

    def update(self) -> None:
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

        if buffer:
            self.terminal.write(buffer)
