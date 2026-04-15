from abc import ABC, abstractmethod


class State(ABC):
    def __init__(self, app):
        self.input_handler = app.input_handler
        self.screen = app.screen

    @abstractmethod
    def on_enter(self):
        pass

    @abstractmethod
    def on_exit(self):
        pass

    @abstractmethod
    def handle_input(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def render(self):
        pass
