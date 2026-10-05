"""
Clock and frame pacing subsystem for Sanctuary.
Provides frame rate control, delta time (dt) calculation, and FPS telemetry.
"""
import time
from typing import Self


class Clock:
    """
    Base cross-platform frame clock.
    Provides standard frame pacing, delta time (dt) measurement, and smoothed FPS telemetry.
    """

    def __init__(self, target_fps: float = 60.0) -> None:
        assert target_fps > 0, "target_fps must be positive"
        self.target_fps = target_fps
        self.target_frame_time = 1.0 / self.target_fps

        now = time.perf_counter()
        self._last_tick = now
        self._next_tick = now

        self.dt = self.target_frame_time
        self.fps = self.target_fps

        self._frame_count = 0
        self._window_start = now

    def _wait(self, time_left: float) -> None:
        """Suspends execution for the remainder of the frame. Overridden by platform subclasses."""
        if time_left > 0:
            time.sleep(time_left)

    def tick(self) -> float:
        """Paces the frame rate to target_fps and returns the elapsed delta time in seconds."""
        self._next_tick += self.target_frame_time
        time_left = self._next_tick - time.perf_counter()

        self._wait(time_left)

        now = time.perf_counter()
        self.dt = now - self._last_tick
        self._last_tick = now

        if now > self._next_tick + self.target_frame_time:
            self._next_tick = now

        self._frame_count += 1
        window_elapsed = now - self._window_start
        if window_elapsed >= 0.25:
            self.fps = self._frame_count / window_elapsed
            self._frame_count = 0
            self._window_start = now

        return self.dt

    def close(self) -> None:
        """Lifecycle cleanup hook."""
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()


class WindowsClock(Clock):
    """
    Windows-specific frame clock.
    Encapsulates winmm 1ms multimedia timer resolution and uses hybrid
    coarse-sleep + micro-wait pacing to bypass the Windows 15.6ms scheduler quantum.
    """

    def __init__(self, target_fps: float = 60.0) -> None:
        super().__init__(target_fps)
        import ctypes

        self._winmm = ctypes.windll.winmm
        self._winmm.timeBeginPeriod(1)
        self._is_active = True

    def _wait(self, time_left: float) -> None:
        if time_left > 0.002:
            time.sleep(time_left - 0.001)
        while time.perf_counter() < self._next_tick:
            pass

    def close(self) -> None:
        if self._is_active:
            self._winmm.timeEndPeriod(1)
            self._is_active = False
