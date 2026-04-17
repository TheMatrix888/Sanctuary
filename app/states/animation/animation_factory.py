from .animation import Animation
from engine.screen_objects import ScreenObject, Text
from .frame_generator import FrameGenerator
from app.core import StateContext

FPS = 60


def create_animation_factories():
    factories = []

    def demo0_factory(context: StateContext):
        return Animation(context, Demo0, 10)

    demo0_factory.name = "Demo0"
    demo0_factory.context_type = StateContext

    def text_demo_factory(context: StateContext):
        return Animation(context, TextDemo, 10)

    text_demo_factory.name = "TextDemo"
    text_demo_factory.context_type = StateContext

    factories.append(demo0_factory)
    factories.append(text_demo_factory)

    return factories


class Demo0(FrameGenerator):
    def __call__(self, progress: float, columns: int, lines: int):
        x = -3 + int((columns + 4) * progress)
        y = -3 + int((lines + 4) * progress)
        animation_info = f"x {x}, y {y}"
        capsule = ScreenObject(
            (x, y),
            [
                "/-\\",
                "|#|",
                "\\-/"
            ])
        return [capsule], animation_info


class TextDemo(FrameGenerator):
    def __call__(self, progress: float, columns: int, lines: int):
        text = Text(
            (0, 0),
            raw_text="This is a sample text and it is much longer than number of cmd columns, but it still fits!!!\nMultiple\nLines\nCheck"
        )
        text.layout(columns)
        return [text], ""
