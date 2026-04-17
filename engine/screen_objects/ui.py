from .screen_object import ScreenObject

class Text(ScreenObject):
    def __init__(
            self,
            text: str | None = None,
            pos: tuple[int, int] | None = None,
    ):
        super().__init__(pos)
        self.text = text

