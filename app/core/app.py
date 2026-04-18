from typing import Type

from .state import State
from .contexts import StateContext, NavigationContext, ScreenContext
from .input_handler import InputHandler
from .factory_protocol import FactoryProtocol
from engine.screen import Screen
from engine.screen_objects import StatusBar


class App:
    def __init__(self, input_handler: InputHandler, screen: Screen):
        self.running = True
        self.state_stack = []
        self.input_handler = input_handler
        self.screen = screen
        self.status_bar = StatusBar()

    def push_state(self, state: State):
        current_state = self.current_state
        if current_state:
            self.status_bar.pop_segment(current_state.status_segment_key)
        self.state_stack.append(state)
        state.on_enter()

    def pop_state(self):
        if self.state_stack:
            state = self.state_stack.pop()
            self.status_bar.pop_segment(state.status_segment_key)
            state.on_exit()

    def create_state_context(self, context_type: Type[StateContext]):
        screen_context = ScreenContext(
            columns=self.screen.columns,
            lines=self.screen.lines,
            draw=self.screen.draw,
            place=self.screen.place
        )

        base_kwargs = dict(
            input_handler=self.input_handler,
            screen_context=screen_context,
            set_status=self.set_status,
            pop_state=self.pop_state
        )

        if context_type is StateContext:
            return StateContext(**base_kwargs)

        if context_type is NavigationContext:
            return NavigationContext(
                **base_kwargs,
                push_state=self.push_state,
                push_state_factory=self.push_state_factory,
                stop=self.stop
            )

        raise ValueError(f"Unsupported context type: {context_type}")

    def push_state_factory(self, factory: FactoryProtocol):
        context = self.create_state_context(factory.context_type)
        state = factory(context)
        self.push_state(state)

    @property
    def current_state(self) -> State | None:
        return self.state_stack[-1] if self.state_stack else None

    def stop(self):
        while self.state_stack:
            state = self.state_stack.pop()
            state.on_exit()
        self.running = False

    def set_status(self, text: str):
        segment_key = self.current_state.status_segment_key
        if segment_key:
            self.status_bar.set_segment(segment_key, text)

    def render_status_bar(self):
        self.status_bar.layout(self.screen.columns)
        self.screen.place(self.status_bar, "bottom_left")
        self.screen.draw(self.status_bar)
