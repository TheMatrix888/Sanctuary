from engine.primitives.symbol import Symbol


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
            pos: tuple[int, int] | None = None,
            content: str | list[str] | list[list[Symbol]] | None = None
    ):
        self.pos = pos
        self.content = self._normalize_content(content)
        self.columns, self.lines = self._calculate_size()

    def _normalize_content(self, content):
        if not content:
            return []

        if isinstance(content, str):
            content = [
                [Symbol(char) for char in content]
            ]

        if all(isinstance(line, str) for line in content):
            content = [
                [Symbol(char) for char in line]
                for line in content
            ]

        if not all(isinstance(line, list) for line in content):
            raise TypeError("Unsupported content format")

        max_width = max(len(line) for line in content)
        padded_content = [
            line + [self.EMPTY_SYMBOL for _ in range(max_width - len(line))]
            for line in content
        ]

        return padded_content

    def _calculate_size(self):
        if not self.content:
            return 0, 0
        columns = len(self.content[0])  # As content was already padded in _normalize_content()
        lines = len(self.content)
        return columns, lines

    def move(self, pos: tuple[int, int]):
        self.pos = pos

    def update_content(self, content: str | list[str] | list[list[Symbol]]):
        self.content = self._normalize_content(content)
        self.columns, self.lines = self._calculate_size()
