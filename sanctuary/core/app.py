"""
Application lifecycle manager for Sanctuary.
Drives the central state stack, input polling, physics update, and differential rendering loop.
"""
from sanctuary.core.input_handler import Key
from sanctuary.core.platform import Platform
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Push, Change, Pop, Quit, State, ToggleMetrics
from sanctuary.ui.telemetry import draw_telemetry_hud


class App:
    def __init__(self, platform: Platform):
        self.screen = Screen(platform.terminal)
        self.clock = platform.clock
        self.dt = 0.0
        self.input_handler = platform.input_handler
        self.states: list[State] = []
        self.metrics_toggle = False

    def run(self) -> None:
        try:
            while self.states:
                self.update()
        finally:
            self.clock.close()
            self.screen.terminal.close()

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
        elif self.input_handler.just_pressed(Key.F3):
            self.toggle_metrics()

        self.screen.check_resize()

        with self.clock.measure("logic"):
            state.update(self.dt, self.screen.size)

        with self.clock.measure("render"):
            self.screen.clear()
            state.draw(self.screen)
            if self.metrics_toggle:
                draw_telemetry_hud(self.screen, self.clock.metrics)
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
            case ToggleMetrics():
                self.toggle_metrics()

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

    def toggle_metrics(self) -> None:
        self.metrics_toggle = not self.metrics_toggle
