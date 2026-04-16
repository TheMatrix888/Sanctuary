from .animation import Animation
from engine.screen_objects import ScreenObject


def create_animations(app, fps=24):
    return [
        Animation(app, demo0, 10, fps)
    ]


def demo0(frame: int, fps: int, duration: int, columns: int, lines: int):
    total_frames = fps * duration
    progress = frame / total_frames
    x = -3 + int((columns + 1) * progress)
    y = -3 + int((lines + 1) * progress)
    capsule = ScreenObject(x, y, [
        "/-\\",
        "|#|",
        "\\-/"
    ])
    cords = ScreenObject(0, lines - 1, [f"x {x} y {y}"])
    frame += 1
    if frame > total_frames:
        frame = 0
    return frame, [capsule, cords]
