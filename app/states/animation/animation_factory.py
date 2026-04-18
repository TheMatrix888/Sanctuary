from .animation import Animation
from engine.screen_objects import ScreenObject, Text
from .frame_generator import FrameGenerator
from app.core import StateContext
from ...core.contexts import ScreenContext


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

    def object_placement_factory(context: StateContext):
        return Animation(context, ObjectPlacementDemo, 10)

    object_placement_factory.name = "ObjectPlacementDemo"
    object_placement_factory.context_type = StateContext

    factories.append(demo0_factory)
    factories.append(text_demo_factory)
    factories.append(object_placement_factory)

    return factories


class Demo0(FrameGenerator):
    def __call__(self, screen: ScreenContext, progress: float):
        x = -3 + int((screen.columns + 4) * progress)
        y = -3 + int((screen.lines + 4) * progress)
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
    def __call__(self, screen: ScreenContext, progress: float):
        text = Text(
            (0, 0),
            raw_text="This is a sample text and it is much longer than number of cmd columns, but it still fits!!!\nMultiple\nLines\nCheck"
        )
        text.layout(screen.columns)
        return [text], ""


class ObjectPlacementDemo(FrameGenerator):
    def __call__(self, screen: ScreenContext, progress: float):
        content = [
            "/-\\",
            "|#|",
            "\\-/"
        ]
        adjust_map = [
            "top_left", "top", "top_right",
            "left", "center", "right",
            "bottom", "bottom_left", "bottom", "bottom_right"
        ]
        capsules = [ScreenObject(content=content) for _ in range(10)]
        for i in range(10):
            screen.place(capsules[i], adjust_map[i])
        return capsules, ""
