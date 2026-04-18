from typing import Type

from app.core import State
from app.states.animation.frame_generator import FrameGenerator


class Animation(State):
    FPS = 60

    def __init__(self, app, frame_generator: Type[FrameGenerator], duration_seconds: float):
        super().__init__(app)
        self.columns, self.lines = self.screen.columns, self.screen.lines

        self.name = type(frame_generator).__name__
        self.frame_generator = frame_generator()

        self.total_frames = duration_seconds * self.FPS
        self.frame = 0

        self.status_segment_key = "animation"

    def on_enter(self):
        self.columns, self.lines = self.screen.columns, self.screen.lines
        self.frame = 0

    def on_exit(self):
        pass

    def handle_input(self):
        input_handler = self.input_handler
        if input_handler.is_pressed("q") or input_handler.is_pressed("esc"):
            self.pop_state()

    def update(self):
        pass

    def render(self):
        progress = self.frame / self.total_frames
        screen_objects, animation_info = self.frame_generator(progress, self.columns, self.lines)

        self.screen.clear()

        for screen_object in screen_objects:
            self.screen.draw(screen_object)

        self.set_status("press q/esc to exit " + animation_info)

        self.screen.update()

        self.frame += 1
        if self.frame > self.total_frames:
            self.frame = 0
