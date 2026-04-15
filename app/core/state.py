from abc import ABC, abstractmethod


class State(ABC):
    def __init__(self, app):
        self.app = app

    @abstractmethod
    def on_enter(self):
        pass

    @abstractmethod
    def on_exit(self):
        pass

    @abstractmethod
    def handle_input(self, input_handler):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def get_screen_objects(self):
        pass
