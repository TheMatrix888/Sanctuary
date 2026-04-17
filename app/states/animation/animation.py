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

    def on_enter(self):
        self.columns, self.lines = self.screen.columns, self.screen.lines
        self.frame = 0
        self.status_bar.set_segment("exit_guide", "press q/esc to exit")

    def on_exit(self):
        self.status_bar.pop_segment("exit_guide")
        self.status_bar.pop_segment("animation_info")

    def handle_input(self):
        input_handler = self.input_handler
        if not input_handler.idle:
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

        self.status_bar.set_segment("animation_info", animation_info)
        self.status_bar.layout(self.screen.columns)
        self.screen.place(self.status_bar, "bottom_left")
        self.screen.draw(self.status_bar)

        self.screen.update()

        self.frame += 1
        if self.frame > self.total_frames:
            self.frame = 0
