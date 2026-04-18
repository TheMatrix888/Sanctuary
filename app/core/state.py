from abc import ABC, abstractmethod
from .contexts import StateContext


class State(ABC):
    status_segment_key: str

    def __init__(self, context: StateContext):
        self.input_handler = context.input_handler
        self.screen = context.screen_context
        self.set_status = context.set_status
        self.pop_state = context.pop_state

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
