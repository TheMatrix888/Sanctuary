"""
Clock and frame pacing subsystem for Sanctuary.
Provides frame rate control, delta time (dt) calculation, and FPS telemetry.
"""
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Self


@dataclass(slots=True, frozen=True)
class FrameMetrics:
    fps: float
    logic_ms: float
    render_ms: float
    work_ms: float
    budget_ms: float
    headroom_ms: float
    load_percent: float


class Timer:
    """
    Non-blocking recurring interval timer driven by frame delta time (dt).
    """

    def __init__(self, interval: float, auto_reset: bool = True) -> None:
        assert interval > 0, "interval must be positive"
        self.interval = interval
        self.auto_reset = auto_reset
        self.elapsed = 0.0

    def tick(self, dt: float) -> bool:
        """
        Advances the timer by dt and returns True if the interval has elapsed.
        Applies modulo arithmetic on auto_reset to prevent debt accumulation during lag spikes.
        """
        self.elapsed += dt
        if self.elapsed >= self.interval:
            if self.auto_reset:
                self.elapsed %= self.interval
            return True
        return False

    def reset(self) -> None:
        """Resets elapsed time to zero."""
        self.elapsed = 0.0

    @property
    def progress(self) -> float:
        """Returns normalized progress [0.0, 1.0] towards interval completion."""
        return min(1.0, self.elapsed / self.interval)


class Clock:
    """
    Base cross-platform frame clock.
    Provides standard frame pacing, delta time (dt) measurement, and smoothed FPS telemetry.
    """

    def __init__(self, target_fps: float = 60.0, metrics_interval: float = 0.25) -> None:
        assert target_fps > 0, "target_fps must be positive"
        self.target_fps = target_fps
        self.target_frame_time = 1.0 / self.target_fps

        now = time.perf_counter()
        self._last_tick = now
        self._next_tick = now

        self.dt = self.target_frame_time
        self.fps = self.target_fps

        budget_ms = self.target_frame_time * 1000.0
        self.metrics = FrameMetrics(
            fps=self.target_fps,
            logic_ms=0.0,
            render_ms=0.0,
            work_ms=0.0,
            budget_ms=budget_ms,
            headroom_ms=budget_ms,
            load_percent=0.0,
        )

        self.phases_accumulator: dict[str, float] = {}
        self.metrics_timer = Timer(metrics_interval)
        self._interval_frames = 0

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
        raw_dt = now - self._last_tick
        self.dt = min(raw_dt, 0.1)
        self._last_tick = now

        if now > self._next_tick + self.target_frame_time:
            self._next_tick = now

        self._interval_frames += 1
        if self.metrics_timer.tick(self.dt):
            fps = self._interval_frames / self.metrics_timer.interval
            self.fps = fps

            avg_update_ms = (self.phases_accumulator.get("logic", 0.0) / self._interval_frames) * 1000.0
            avg_draw_ms = (self.phases_accumulator.get("render", 0.0) / self._interval_frames) * 1000.0
            work_ms = avg_update_ms + avg_draw_ms
            budget_ms = self.target_frame_time * 1000.0
            headroom_ms = max(0.0, budget_ms - work_ms)
            load_percent = (work_ms / budget_ms * 100.0) if budget_ms > 0 else 0.0

            self.metrics = FrameMetrics(
                fps=fps,
                logic_ms=avg_update_ms,
                render_ms=avg_draw_ms,
                work_ms=work_ms,
                budget_ms=budget_ms,
                headroom_ms=headroom_ms,
                load_percent=load_percent,
            )

            self.phases_accumulator.clear()
            self._interval_frames = 0

        return self.dt

    def record_phase(self, phase: str, elapsed: float) -> None:
        """Accumulates execution duration in seconds for a specific frame phase."""
        self.phases_accumulator[phase] = self.phases_accumulator.get(phase, 0.0) + elapsed

    @contextmanager
    def measure(self, phase: str):
        """Context manager to measure and attribute execution duration of a frame phase."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.record_phase(phase, elapsed)

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

    def __init__(self, target_fps: float = 60.0, metrics_interval: float = 1.0) -> None:
        super().__init__(target_fps, metrics_interval)
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
