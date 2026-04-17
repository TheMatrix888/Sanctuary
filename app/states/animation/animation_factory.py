from .animation import Animation
from engine.screen_objects import ScreenObject

FPS = 60


def create_animations(app, fps=24):
    return [
        Animation(app, demo0, 10)
    ]


def demo0(frame: int, duration_seconds: int, columns: int, lines: int):
    total_frames = FPS * duration_seconds
    progress = frame / total_frames
    x = -3 + int((columns + 4) * progress)
    y = -3 + int((lines + 4) * progress)
    capsule = ScreenObject(
        (x, y),
        [
            "/-\\",
            "|#|",
            "\\-/"
        ])
    cords = ScreenObject((0, lines - 2), [f"x {x} y {y}"])
    frame += 1
    if frame > total_frames:
        frame = 0
    return frame, [capsule, cords]
