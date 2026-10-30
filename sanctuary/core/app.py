"""
Application lifecycle manager for Sanctuary.
Drives the central state stack, input polling, physics update, and differential rendering loop.
"""
from multiprocessing import Process

from sanctuary.core.config import DEFAULT_DISPLAY_CONFIG, DisplayConfig
from sanctuary.core.input_handler import Key
from sanctuary.core.platform import Platform
from sanctuary.core.screen import Screen
from sanctuary.core.state import Command, Push, Change, Pop, Quit, State, ToggleMetrics, StartProcess, TerminateProcess
from sanctuary.ui.telemetry import draw_telemetry_hud


class App:
    def __init__(self, platform: Platform, display_config: DisplayConfig = DEFAULT_DISPLAY_CONFIG):
        self.screen = Screen(platform.terminal, config=display_config)
        self.clock = platform.clock
        self.dt = 0.0
        self.input_handler = platform.input_handler
        self.states: list[State] = []
        self.metrics_toggle = False
        self.processes: dict[str, Process] = {}

    def run(self) -> None:
        try:
            while self.states:
                self.update()
        finally:
            self.quit()
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

        with self.clock.measure("draw"):
            self.screen.clear()
            state.draw(self.screen)
            if self.metrics_toggle:
                draw_telemetry_hud(self.screen, self.clock.metrics)
            self.screen.compose()

        with self.clock.measure("flush"):
            self.screen.flush()

        self.dt = self.clock.tick()

    @staticmethod
    def _stop_process(process: Process) -> None:
        if process.is_alive():
            process.join(timeout=0.2)
            if process.is_alive():
                process.terminate()
                process.join(timeout=0.5)

    def _execute(self, command: Command) -> None:
        match command:
            case Push(state):
                self.push_state(state)
            case Change(state):
                self.change_state(state)
            case Pop():
                self.pop_state()
            case Quit():
                self.quit()
            case ToggleMetrics():
                self.toggle_metrics()
            case StartProcess(process):
                old_proc = self.processes.pop(process.name, None)
                if old_proc:
                    self._stop_process(old_proc)
                self.processes[process.name] = process
                process.start()
            case TerminateProcess(name):
                proc = self.processes.pop(name, None)
                if proc:
                    self._stop_process(proc)

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
        for process in list(self.processes.values()):
            self._stop_process(process)
        self.processes.clear()


    def toggle_metrics(self) -> None:
        self.metrics_toggle = not self.metrics_toggle
