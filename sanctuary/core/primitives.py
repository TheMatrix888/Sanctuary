"""
Graphical raster primitives for Sanctuary.
Provides Color, Cell (atomic glyph + color state), and Surface (2D RAM drawing canvas).
"""
import textwrap
from dataclasses import dataclass
from typing import Iterator, Self

from sanctuary.core.geometry import Size


@dataclass(slots=True, frozen=True)
class Color:
    """
    Immutable 24-bit TrueColor RGB representation.
    Guarantees color components are strictly bounded within [0, 255].
    """
    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        assert 0 <= self.r <= 255, f"Red component must be in range [0, 255], got: {self.r}"
        assert 0 <= self.g <= 255, f"Green component must be in range [0, 255], got: {self.g}"
        assert 0 <= self.b <= 255, f"Blue component must be in range [0, 255], got: {self.b}"

    def __iter__(self) -> Iterator[int]:
        """Allows unpacking as RGB tuple: r, g, b = color."""
        yield self.r
        yield self.g
        yield self.b

    @property
    def inverted(self) -> "Color":
        """Returns the complementary inverse 24-bit RGB color."""
        return Color(255 - self.r, 255 - self.g, 255 - self.b)


DEFAULT_FG = Color(204, 204, 204)
DEFAULT_BG = Color(12, 12, 12)


@dataclass(slots=True, frozen=True)
class Cell:
    """
    Atomic immutable rendering unit in character cell space.
    Encapsulates a single glyph character and guaranteed foreground/background colors.
    """
    char: str = " "
    fg_color: Color = DEFAULT_FG
    bg_color: Color = DEFAULT_BG

    def __post_init__(self) -> None:
        if len(self.char) > 1:
            object.__setattr__(self, "char", self.char[0])
        elif not self.char:
            object.__setattr__(self, "char", " ")

        if self.fg_color is None:
            object.__setattr__(self, "fg_color", DEFAULT_FG)
        if self.bg_color is None:
            object.__setattr__(self, "bg_color", DEFAULT_BG)


class Surface:
    """
    2D raster grid of Cell elements in RAM.
    Constructed directly from multiline text art by default.
    Empty/blank surfaces are instantiated via Surface.empty(size) for framebuffers.
    """
    size: Size
    cells: list[list[Cell]]

    def __init__(
        self,
        text: str,
        fg_color: Color | None = None,
        bg_color: Color | None = None,
    ) -> None:
        """
        Creates a Surface from a multiline string.
        Automatically dedents indentation whitespace and trims boundary newlines.
        Dimensions are automatically inferred from line count and maximum line length.
        """
        lines = textwrap.dedent(text).strip("\n").splitlines()
        height = len(lines)
        width = max((len(line) for line in lines), default=0)
        self.size = Size(width, height)

        self.cells = [
            [Cell(" ", fg_color, bg_color) for _ in range(self.size.columns)]
            for _ in range(self.size.rows)
        ]

        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                self.cells[y][x] = Cell(char, fg_color, bg_color)

    @classmethod
    def empty(
        cls,
        size: Size,
        fill_char: str = " ",
    ) -> Self:
        """
        Creates a blank Surface with explicit dimensions.
        Reserved primarily for front/back screen buffers.
        """
        surface = cls.__new__(cls)
        surface.size = size
        surface.cells = [
            [Cell(fill_char) for _ in range(size.columns)]
            for _ in range(size.rows)
        ]
        return surface

    def clear(self, fill_cell: Cell = Cell(" ")) -> None:
        """Resets all cells to blank spaces (or designated fill_char)."""
        for row in self.cells:
            for x in range(self.size.columns):
                row[x] = fill_cell

    def set_cell(self, x: int, y: int, cell: Cell) -> None:
        """Safely places a cell with boundary clipping."""
        if 0 <= x < self.size.columns and 0 <= y < self.size.rows:
            self.cells[y][x] = cell

    def get_cell(self, x: int, y: int) -> Cell | None:
        """Safely retrieves a cell with boundary clipping."""
        if 0 <= x < self.size.columns and 0 <= y < self.size.rows:
            return self.cells[y][x]
        return None

    def apply_color(
        self,
        fg_color: Color | None = None,
        bg_color: Color | None = None,
    ) -> None:
        """Applies uniform foreground and/or background colors across all cells."""
        for row in self.cells:
            for x in range(self.size.columns):
                cell = row[x]
                row[x] = Cell(
                    cell.char,
                    fg_color if fg_color is not None else cell.fg_color,
                    bg_color if bg_color is not None else cell.bg_color,
                )

    def apply_color_mask(
        self,
        fg_color_mask: list[list[Color | None]] | None = None,
        bg_color_mask: list[list[Color | None]] | None = None,
    ) -> None:
        """Applies 2D color masks to modulate cell colors."""
        def get_color(mask: list[list[Color | None]] | None, x: int, y: int) -> Color | None:
            if mask and 0 <= y < len(mask) and 0 <= x < len(mask[y]):
                return mask[y][x]
            return None

        for y, row in enumerate(self.cells):
            for x, cell in enumerate(row):
                new_fg = get_color(fg_color_mask, x, y)
                new_bg = get_color(bg_color_mask, x, y)
                if new_fg is not None or new_bg is not None:
                    row[x] = Cell(
                        char=cell.char,
                        fg_color=new_fg if new_fg is not None else cell.fg_color,
                        bg_color=new_bg if new_bg is not None else cell.bg_color,
                    )

    def flip_x(self, mirror_glyphs: bool = True) -> Self:
        """
        Returns a new Surface flipped horizontally.
        Optionally mirrors symmetric ASCII characters like / <-> \\, ( <-> ).
        """
        pairs = {
            "/": "\\", "\\": "/",
            "(": ")", ")": "(",
            "[": "]", "]": "[",
            "{": "}", "}": "{",
            "<": ">", ">": "<",
        }
        flipped = self.empty(self.size)
        for y, row in enumerate(self.cells):
            for x, cell in enumerate(reversed(row)):
                char = pairs.get(cell.char, cell.char) if mirror_glyphs else cell.char
                flipped.set_cell(x, y, Cell(char=char, fg_color=cell.fg_color, bg_color=cell.bg_color))
        return flipped
