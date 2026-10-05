"""
Application lifecycle manager for Sanctuary.
Drives the central state stack, input polling, physics update, and differential rendering loop.
"""
from sanctuary.core.platform import Platform
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Push, Change, Pop, Quit, State


class App:
    def __init__(self, platform: Platform):
        self.screen = Screen(platform.terminal)
        self.clock = platform.clock
        self.dt = 0.0
        self.input_handler = platform.input_handler
        self.states: list[State] = []

    def run(self) -> None:
        try:
            while self.states:
                self.update()
        finally:
            self.clock.close()

    def update(self) -> None:
        if not self.states:
            return
        state = self.states[-1]

        self.input_handler.update()
        command = state.handle_input(self.input_handler)
        if command:
            self._execute(command)
            if not self.states:
                return
            state = self.states[-1]

        state.update(self.dt, self.screen.size)

        self.screen.clear()
        state.draw(self.screen)
        self.screen.update()

        self.dt = self.clock.tick()

    def _execute(self, command: Command) -> None:
        match command:
            case Push(next_state):
                self.push_state(next_state)
            case Change(next_state):
                self.change_state(next_state)
            case Pop():
                self.pop_state()
            case Quit():
                self.quit()

    def push_state(self, state: State) -> None:
        self.states.append(state)
        state.on_enter()

    def change_state(self, state: State) -> None:
        self.pop_state()
        self.push_state(state)

    def pop_state(self) -> None:
        if len(self.states) > 0:
            state = self.states.pop()
            state.on_exit()

    def quit(self) -> None:
        while len(self.states) > 0:
            self.pop_state()
