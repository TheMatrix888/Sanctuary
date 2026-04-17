from .text import Text


class StatusBar(Text):
    def __init__(self):
        super().__init__()
        self.segments = {}

    def set_segment(self, key: str, text: str):
        self.segments[key] = text

    def pop_segment(self, key: str):
        self.segments.pop(key, None)

    def _compose_text(self):
        lines = [value for value in self.segments.values()]
        composed_text = " ".join(lines)
        return composed_text

    def layout(self, screen_columns: int):
        self.raw_text = self._compose_text()
        super().layout(screen_columns)
