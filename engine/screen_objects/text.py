from .screen_object import ScreenObject


class Text(ScreenObject):
    def __init__(
            self,
            pos: tuple[int, int] | None = None,
            text: str | None = None
    ):
        super().__init__(pos)
        self.text = text

    def layout(self, width_columns: int):
        lines = self.wrap_text(width_columns)
        self.content = self._normalize_content(lines)
        self.columns, self.lines = self._calculate_size()

    def wrap_text(self, width_columns: int):
        return [
            self.text[i:i + width_columns]
            for i in range(0, len(self.text), width_columns)
        ]
