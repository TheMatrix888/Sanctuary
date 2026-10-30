"""
Unit tests for App background process management and graceful termination.
"""
from sanctuary.core.app import App
from sanctuary.core.config import DisplayConfig
from sanctuary.core.input_handler import Key
from sanctuary.core.platform import Platform
from sanctuary.core.state import Command, Quit, StartProcess, State, TerminateProcess
from sanctuary.core.terminal import VirtualTerminal


class MockClock:
    def __init__(self) -> None:
        self.closed = False
        self.metrics = None

    def tick(self) -> float:
        return 0.016

    def measure(self, phase: str):
        class DummyCtx:
            def __enter__(self):
                pass
            def __exit__(self, *args):
                pass
        return DummyCtx()

    def close(self) -> None:
        self.closed = True


class MockInput:
    def update(self) -> None:
        pass

    def just_pressed(self, key: Key) -> bool:
        return False

    def is_pressed(self, key: Key) -> bool:
        return False

    def is_repeated(self, *keys: Key) -> bool:
        return False


class MockProcess:
    def __init__(self, name: str = "mock_proc") -> None:
        self.name = name
        self.is_started = False
        self.is_terminated = False
        self.joined = False
        self._alive = False

    def start(self) -> None:
        self.is_started = True
        self._alive = True

    def is_alive(self) -> bool:
        return self._alive

    def join(self, timeout: float | None = None) -> None:
        self.joined = True
        self._alive = False

    def terminate(self) -> None:
        self.is_terminated = True
        self._alive = False


def create_test_app() -> App:
    terminal = VirtualTerminal()
    clock = MockClock()
    input_handler = MockInput()
    platform = Platform(terminal=terminal, clock=clock, input_handler=input_handler)  # type: ignore
    return App(platform=platform, display_config=DisplayConfig(columns=80, rows=25))


def test_app_start_and_terminate_process_commands() -> None:
    app = create_test_app()
    proc = MockProcess(name="custom_worker")

    # Execute StartProcess
    app._execute(StartProcess(proc))  # type: ignore
    assert proc.is_started is True
    assert "custom_worker" in app.processes
    assert app.processes["custom_worker"] is proc

    # Execute TerminateProcess
    app._execute(TerminateProcess("custom_worker"))
    assert proc.joined is True
    assert "custom_worker" not in app.processes


def test_app_quit_terminates_all_running_processes() -> None:
    app = create_test_app()
    p1 = MockProcess("p1")
    p2 = MockProcess("p2")

    app._execute(StartProcess(p1))  # type: ignore
    app._execute(StartProcess(p2))  # type: ignore
    assert len(app.processes) == 2

    # Quit application
    app.quit()
    assert p1.joined is True
    assert p2.joined is True
    assert len(app.processes) == 0


def test_app_finally_block_cleans_up_processes_on_exit() -> None:
    app = create_test_app()
    proc = MockProcess("p_orphan")
    app._execute(StartProcess(proc))  # type: ignore

    class QuittingState(State):
        def handle_input(self, input_handler) -> Command | None:
            return Quit()

    app.push_state(QuittingState())
    app.run()

    # After main loop exits, finally block must have terminated the process
    assert proc.joined is True
    assert len(app.processes) == 0
