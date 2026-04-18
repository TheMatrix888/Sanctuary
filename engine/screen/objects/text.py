from .screen_object import ScreenObject


class Text(ScreenObject):
    def __init__(
            self,
            pos: tuple[int, int] | None = None,
            raw_text: str | None = None
    ):
        super().__init__(pos)
        self.raw_text = "" if raw_text is None else raw_text

    def set_text(self, raw_text: str):
        self.raw_text = raw_text

    def layout(self, width_columns: int):
        content = []
        for line in self.raw_text.split("\n"):
            content.extend(self.wrap_text(line, width_columns))

        self.content = self._normalize_content(content)
        self._recalculate()

    def wrap_text(self, text: str, width_columns: int):
        if text == "":
            return [""]
        return [
            text[i:i + width_columns]
            for i in range(0, len(text), width_columns)
        ]
