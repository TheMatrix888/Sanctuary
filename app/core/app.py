from typing import Type

from .state_context import StateContext, MenuContext
from .input_handler import InputHandler
from engine.screen import Screen
from engine.screen_objects import StatusBar
from .state import State
from .state_factory import StateFactory


class App:
    def __init__(self, input_handler: InputHandler, screen: Screen):
        self.running = True
        self.state_stack = []
        self.input_handler = input_handler
        self.screen = screen
        self.status_bar = StatusBar()

    def push_state(self, state: State):
        if self.state_stack:
            self.current_state.on_exit()

        self.state_stack.append(state)
        state.on_enter()

    def pop_state(self):
        if self.state_stack:
            state = self.state_stack.pop()
            state.on_exit()
            self.current_state.on_enter()

    def create_state_context(self, context_type: Type[StateContext]):
        if context_type == StateContext:
            return StateContext(
                input_handler=self.input_handler,
                screen=self.screen,
                status_bar=self.status_bar,
                pop_state=self.pop_state
            )

        if context_type == MenuContext:
            return MenuContext(
                input_handler=self.input_handler,
                screen=self.screen,
                status_bar=self.status_bar,
                pop_state=self.pop_state,
                push_state=self.push_state,
                push_state_factory=self.push_state_factory,
                stop=self.stop
            )

        return None

    def push_state_factory(self, factory: StateFactory):
        context = self.create_state_context(factory.context_type)
        state = factory(context)
        self.push_state(state)

    @property
    def current_state(self) -> State:
        return self.state_stack[-1]

    def stop(self):
        while self.state_stack:
            state = self.state_stack.pop()
            state.on_exit()
        self.running = False
