from .ansi import fg_color, bg_color, reset_color


class Symbol:
    """
    Represents a single character with foreground and background colors.

    Parameters:
        char: Single character string.
        text_color: (r, g, b) tuple or None.
        background_color: (r, g, b) tuple or None.
    """
    DEFAULT_COLOR_FG = (255, 255, 255)
    DEFAULT_COLOR_BG = (12, 12, 12)

    def __init__(self, char: str,
                 text_color=None,
                 background_color=None
                 ):
        self.char = char
        self.text_color = text_color or self.DEFAULT_COLOR_FG
        self.background_color = background_color or self.DEFAULT_COLOR_BG

    def __eq__(self, other):
        return (
                self.char == other.char and
                self.text_color == other.text_color and
                self.background_color == other.background_color
        )

    def rendered(self):
        return fg_color(*self.text_color) + bg_color(*self.background_color) + self.char + reset_color()
