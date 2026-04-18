from app.core.contexts import ScreenContext
from engine.screen.objects import ScreenObject


class FrameGenerator:
    def __call__(self, screen: ScreenContext, progress: float) -> tuple[list[ScreenObject], str]:
        raise NotImplementedError
