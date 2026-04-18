from engine.primitives import Position, Size, Symbol


class ScreenObject:
    """
    Drawable object positioned on the engine screen.

    Parameters:
        pos: tuple[int, int] Position on the screen (top-left corner).
        content:
            - str
            - list[str] -> will be converted to Symbol grid
            - list[list[Symbol]] -> used as-is
    """
    EMPTY_SYMBOL = Symbol(" ")

    def __init__(
            self,
            pos: Position | None = None,
            content: str | list[str] | list[list[Symbol]] | None = None
    ):
        self.pos = pos
        self.size = None
        self.content = self._normalize_content(content)
        self._recalculate()

    def _normalize_content(self, content):
        if not content:
            return []

        if isinstance(content, str):
            return [
                [Symbol(char) for char in content]
            ]

        if all(isinstance(line, str) for line in content):
            return [
                [Symbol(char) for char in line]
                for line in content
            ]

        if all(isinstance(line, list) for line in content):
            return content

        raise TypeError("Unsupported content format")

    def _pad_content(self, content: list[list[Symbol]]) -> list[list[Symbol]] | None:
        if not content:
            return None
        max_width = max(len(line) for line in content)
        padded_content = [
            line + [self.EMPTY_SYMBOL for _ in range(max_width - len(line))]
            for line in content
        ]
        return padded_content

    def _calculate_size(self) -> Size:
        if not self.content:
            return Size(0, 0)
        columns = len(self.content[0])  # As content was already padded in _recalculate()
        lines = len(self.content)
        return Size(columns, lines)

    def _recalculate(self):
        self.content = self._pad_content(self.content)
        self.size = self._calculate_size()

    def move_at(self, pos: Position):
        self.pos = pos

    def move_by(self, x: int, y: int):
        self.pos.x += x
        self.pos.y += y

    def resize(self, size: Size):
        self.size = size

    def set_content(self, content: str | list[str] | list[list[Symbol]]):
        self.content = self._normalize_content(content)
        self._recalculate()

    def insert_content(self, content: str | list[str] | list[list[Symbol]], line: int):
        new = self._normalize_content(content)
        self.content[line:line] = new
        self._recalculate()
