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

    def __init__(
            self,
            pos: tuple[int, int] | None = None,
            content: str | list[str] | list[list[Symbol]] | None = None
    ):
        self.pos = pos
        self.content = self._normalize_content(content)

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

    def move(self, pos: tuple[int, int]):
        self.pos = pos

    def update_content(self, content: str | list[str] | list[list[Symbol]]):
        self.content = self._normalize_content(content)
