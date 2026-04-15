from engine.primitives.symbol import Symbol


class ScreenObject:
    """
    Drawable object positioned on the engine screen.

    Parameters:
        x, y: Position on the screen (top-left corner).
        content:
            - list[str] -> will be converted to Symbol grid
            - list[list[Symbol]] -> used as-is
        screen: Rendering backend.
    """

    def __init__(self, x: int = 0, y: int = 0, content=None, screen=None):
        self.x, self.y = x, y
        self.content = self._normalize_content(content)
        self.screen = screen

    def _normalize_content(self, content):
        if not content:
            return []

        if all(isinstance(line, str) for line in content):
            return [
                [Symbol(char) for char in line]
                for line in content
            ]

        if all(isinstance(line, list) for line in content):
            return content

        raise TypeError("Unsupported content format")

    def move(self, x: int, y: int):
        self.x, self.y = x, y

    def update_content(self, content):
        self.content = self._normalize_content(content)

    def draw(self):
        if self.screen:
            self.screen.draw(self)
