from app.core import State
from time import time


class Animation(State):
    def __init__(self, app, frame_generator, duration_seconds: float, fps: int):
        super().__init__(app)

        self.name = frame_generator.__name__
        self.frame_generator = frame_generator
        self.duration_seconds = duration_seconds
        self.fps = fps
        self.frame_time = 1 / fps

        self.columns, self.lines = self.screen.columns, self.screen.lines
        self.frame = 0
        self.last_render = time()

    def on_enter(self):
        self.columns, self.lines = self.screen.columns, self.screen.lines
        self.frame = 0
        self.last_render = time()

    def on_exit(self):
        pass

    def handle_input(self):
        input_handler = self.input_handler
        if not input_handler.idle:
            if input_handler.is_pressed("q") or input_handler.is_pressed("esc"):
                self.exit_function()

    def update(self):
        pass

    def render(self):
        if time() - self.last_render > self.frame_time:
            self.status_bar.update_content(f"{self.name} Press q/esc to exit")
            self.frame, screen_objects = self.frame_generator(self.frame, self.fps, self.duration_seconds, self.columns, self.lines)
            self.screen.clear()
            for screen_object in screen_objects:
                self.screen.draw(screen_object)
            self.screen.draw(self.status_bar)
            self.screen.update()
            self.last_render = time()
