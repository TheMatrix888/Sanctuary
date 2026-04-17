from engine.screen_objects import ScreenObject


class FrameGenerator:
    def __call__(self, progress: float, columns: int, lines: int) -> tuple[list[ScreenObject], str]:
        raise NotImplementedError
