"""
Input handling subsystem for Sanctuary.
Provides platform-agnostic key enumeration, discrete press detection,
and stateful keystroke tracking.
"""
import ctypes
import time
from abc import ABC, abstractmethod
from ctypes import wintypes
from enum import StrEnum

from sanctuary.core.geometry import Point
from sanctuary.core.terminal import WindowsTerminal

DEFAULT_INITIAL_DELAY: float = 0.20
DEFAULT_REPEAT_INTERVAL: float = 0.05
KEY_PRESSED_MASK: int = 0x8000  # Win32 GetAsyncKeyState high-order bit indicating key down


class Key(StrEnum):
    """Platform-agnostic key identifiers for game actions and menu navigation."""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    ENTER = "enter"
    ESC = "esc"
    SPACE = "space"
    TAB = "tab"
    BRACKET_LEFT = "["
    BRACKET_RIGHT = "]"
    W = "w"
    A = "a"
    S = "s"
    D = "d"
    Q = "q"
    E = "e"
    R = "r"
    H = "h"
    F = "f"
    C = "c"
    P = "p"
    ONE = "1"
    TWO = "2"
    THREE = "3"
    SHIFT = "shift"
    CTRL = "ctrl"
    F1 = "f1"
    F2 = "f2"
    F3 = "f3"
    F4 = "f4"
    F5 = "f5"
    F6 = "f6"
    F7 = "f7"
    F8 = "f8"
    F9 = "f9"
    F10 = "f10"
    F11 = "f11"
    F12 = "f12"


class InputHandler(ABC):
    """
    Abstract base input handler providing frame-bound key tracking and state queries.
    Maintains current, previous, and typematic repeat key snapshots for idempotent lookups.
    """
    current_keys: set[Key]
    previous_keys: set[Key]
    repeated_keys: set[Key]
    mouse_position: Point | None
    mouse_pressed: bool
    mouse_just_pressed: bool
    mouse_right_pressed: bool
    mouse_right_just_pressed: bool
    initial_delay: float
    repeat_interval: float
    _key_press_times: dict[Key, float]
    _key_repeat_times: dict[Key, float]

    def __init__(
        self,
        initial_delay: float = DEFAULT_INITIAL_DELAY,
        repeat_interval: float = DEFAULT_REPEAT_INTERVAL,
    ) -> None:
        self.current_keys = set()
        self.previous_keys = set()
        self.repeated_keys = set()
        self.mouse_position = None
        self.mouse_pressed = False
        self.mouse_just_pressed = False
        self.mouse_right_pressed = False
        self.mouse_right_just_pressed = False
        self.initial_delay = initial_delay
        self.repeat_interval = repeat_interval
        self._key_press_times = {}
        self._key_repeat_times = {}

    @abstractmethod
    def update(self) -> None:
        """Polls input state and updates frame snapshots once per frame."""
        pass

    @staticmethod
    def _normalize_key(key: Key | str) -> Key | None:
        """Normalizes an enum member or string into a valid Key instance."""
        if isinstance(key, Key):
            return key
        try:
            return Key(key.lower())
        except ValueError:
            return None

    def is_pressed(self, *keys: Key | str) -> bool:
        """Returns True if any of the specified keys is currently held down in this frame."""
        for key in keys:
            if isinstance(key, (list, tuple, set)):
                for sub_key in key:
                    normalized = self._normalize_key(sub_key)
                    if normalized and normalized in self.current_keys:
                        return True
            else:
                normalized = self._normalize_key(key)
                if normalized and normalized in self.current_keys:
                    return True
        return False

    def just_pressed(self, *keys: Key | str) -> bool:
        """Returns True only on the initial frame any of the specified keys was pressed down."""
        for key in keys:
            if isinstance(key, (list, tuple, set)):
                for sub_key in key:
                    normalized = self._normalize_key(sub_key)
                    if normalized and (normalized in self.current_keys) and (normalized not in self.previous_keys):
                        return True
            else:
                normalized = self._normalize_key(key)
                if normalized and (normalized in self.current_keys) and (normalized not in self.previous_keys):
                    return True
        return False

    def is_repeated(self, *keys: Key | str) -> bool:
        """
        Returns True on the initial frame any of the specified keys was pressed,
        and periodically at `repeat_interval` cadence once held longer than `initial_delay`.
        Supports passing multiple keys or a collection: is_repeated(Key.RIGHT, Key.D) or is_repeated([Key.RIGHT, Key.D]).
        """
        for key in keys:
            if isinstance(key, (list, tuple, set)):
                for sub_key in key:
                    normalized = self._normalize_key(sub_key)
                    if normalized and normalized in self.repeated_keys:
                        return True
            else:
                normalized = self._normalize_key(key)
                if normalized and normalized in self.repeated_keys:
                    return True
        return False

    def _update_typematic_repeat(self, now: float | None = None) -> None:
        """
        Updates the set of repeated keys for the current frame snapshot.
        """
        if now is None:
            now = time.perf_counter()

        self.repeated_keys.clear()

        # Remove keys that are no longer held down
        released_keys = [k for k in self._key_press_times if k not in self.current_keys]
        for k in released_keys:
            del self._key_press_times[k]
            self._key_repeat_times.pop(k, None)

        for key in self.current_keys:
            if key not in self.previous_keys:
                # Initial press: fire immediately
                self._key_press_times[key] = now
                self._key_repeat_times[key] = now
                self.repeated_keys.add(key)
            else:
                # Held key: check typematic thresholds
                press_time = self._key_press_times.get(key, now)
                last_repeat = self._key_repeat_times.get(key, now)
                if (now - press_time) >= self.initial_delay:
                    if (now - last_repeat) >= self.repeat_interval:
                        self._key_repeat_times[key] = now
                        self.repeated_keys.add(key)


class WindowsInputHandler(InputHandler):
    """
    Windows-specific input handler using Win32 GetAsyncKeyState.
    Scoped strictly to the terminal window when in foreground focus.
    """

    KEY_MAP: dict[Key, int] = {
        Key.UP: 0x26,
        Key.DOWN: 0x28,
        Key.LEFT: 0x25,
        Key.RIGHT: 0x27,
        Key.ENTER: 0x0D,
        Key.ESC: 0x1B,
        Key.SPACE: 0x20,
        Key.TAB: 0x09,
        Key.BRACKET_LEFT: 0xDB,
        Key.BRACKET_RIGHT: 0xDD,
        # Win32 virtual key codes for characters match uppercase ASCII
        Key.W: ord("W"),
        Key.A: ord("A"),
        Key.S: ord("S"),
        Key.D: ord("D"),
        Key.Q: ord("Q"),
        Key.E: ord("E"),
        Key.R: ord("R"),
        Key.H: ord("H"),
        Key.F: ord("F"),
        Key.C: ord("C"),
        Key.P: ord("P"),
        Key.ONE: ord("1"),
        Key.TWO: ord("2"),
        Key.THREE: ord("3"),
        Key.SHIFT: 0x10,  # VK_SHIFT
        Key.CTRL: 0x11,  # VK_CONTROL
        # Function keys F1 to F12 (VK_F1 = 0x70 through VK_F12 = 0x7B)
        Key.F1: 0x70,
        Key.F2: 0x71,
        Key.F3: 0x72,
        Key.F4: 0x73,
        Key.F5: 0x74,
        Key.F6: 0x75,
        Key.F7: 0x76,
        Key.F8: 0x77,
        Key.F9: 0x78,
        Key.F10: 0x79,
        Key.F11: 0x7A,
        Key.F12: 0x7B,
    }

    def __init__(self, terminal: WindowsTerminal) -> None:
        super().__init__()
        self.terminal = terminal
        self._user32 = ctypes.windll.user32
        self._user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self._user32.GetAsyncKeyState.restype = wintypes.SHORT
        self._user32.GetForegroundWindow.argtypes = []
        self._user32.GetForegroundWindow.restype = wintypes.HWND
        self._user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
        self._user32.GetCursorPos.restype = wintypes.BOOL
        self._user32.ScreenToClient.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
        self._user32.ScreenToClient.restype = wintypes.BOOL
        self._user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self._user32.GetClientRect.restype = wintypes.BOOL

    def update(self) -> None:
        """Captures hardware keystroke and mouse state snapshot for the current frame."""
        self.previous_keys = self.current_keys.copy()
        self.current_keys = set()

        # Ignore input when the terminal window is not in foreground focus
        if not self.terminal.hwnd or self._user32.GetForegroundWindow() != self.terminal.hwnd:
            self.mouse_position = None
            self.mouse_pressed = False
            self.mouse_just_pressed = False
            self.mouse_right_pressed = False
            self.mouse_right_just_pressed = False
            self._update_typematic_repeat()
            return

        for key, vk_code in self.KEY_MAP.items():
            if self._user32.GetAsyncKeyState(vk_code) & KEY_PRESSED_MASK:
                self.current_keys.add(key)

        # Mouse position and button tracking
        pt = wintypes.POINT()
        if (
            self._user32.GetCursorPos(ctypes.byref(pt))
            and self._user32.ScreenToClient(self.terminal.hwnd, ctypes.byref(pt))
        ):
            rc_cli = wintypes.RECT()
            if (
                self._user32.GetClientRect(self.terminal.hwnd, ctypes.byref(rc_cli))
                and 0 <= pt.x < rc_cli.right
                and 0 <= pt.y < rc_cli.bottom
            ):
                font_size = self.terminal.get_font_size()
                font_w = max(1, font_size.width)
                font_h = max(1, font_size.height)
                self.mouse_position = Point(pt.x // font_w, pt.y // font_h)
            else:
                self.mouse_position = None
        else:
            self.mouse_position = None

        lbutton_down = bool(self._user32.GetAsyncKeyState(0x01) & KEY_PRESSED_MASK)
        rbutton_down = bool(self._user32.GetAsyncKeyState(0x02) & KEY_PRESSED_MASK)

        active_lbutton = lbutton_down and (self.mouse_position is not None)
        self.mouse_just_pressed = active_lbutton and not self.mouse_pressed
        self.mouse_pressed = active_lbutton

        active_rbutton = rbutton_down and (self.mouse_position is not None)
        self.mouse_right_just_pressed = active_rbutton and not self.mouse_right_pressed
        self.mouse_right_pressed = active_rbutton

        self._update_typematic_repeat()


class VirtualInputHandler(InputHandler):
    """
    Headless in-memory input driver for automated testing and CI pipelines.
    Allows programmatic simulation of key presses and releases without hardware.
    """

    def __init__(
        self,
        initial_delay: float = DEFAULT_INITIAL_DELAY,
        repeat_interval: float = DEFAULT_REPEAT_INTERVAL,
    ) -> None:
        super().__init__(initial_delay=initial_delay, repeat_interval=repeat_interval)
        self._held_keys: set[Key] = set()
        self._virtual_mouse_pos: Point | None = None
        self._virtual_mouse_pressed: bool = False
        self._virtual_mouse_right_pressed: bool = False

    def press(self, key: Key | str) -> None:
        """Simulates physically pressing and holding a key down."""
        normalized = self._normalize_key(key)
        if normalized:
            self._held_keys.add(normalized)

    def release(self, key: Key | str) -> None:
        """Simulates physically releasing a key."""
        normalized = self._normalize_key(key)
        if normalized:
            self._held_keys.discard(normalized)

    def set_mouse_position(self, pos: Point | None) -> None:
        """Sets the simulated mouse position in character cells."""
        self._virtual_mouse_pos = pos

    def press_mouse(self, button: int = 1) -> None:
        """Simulates pressing and holding a mouse button (1 = Left, 2 = Right)."""
        if button == 1:
            self._virtual_mouse_pressed = True
        elif button == 2:
            self._virtual_mouse_right_pressed = True

    def release_mouse(self, button: int = 1) -> None:
        """Simulates releasing a mouse button (1 = Left, 2 = Right)."""
        if button == 1:
            self._virtual_mouse_pressed = False
        elif button == 2:
            self._virtual_mouse_right_pressed = False

    def click_mouse(self, pos: Point | None = None, button: int = 1) -> None:
        """Simulates clicking a mouse button at an optional cell coordinate."""
        if pos is not None:
            self._virtual_mouse_pos = pos
        self.press_mouse(button=button)

    def update(self, now: float | None = None) -> None:
        """Advances the virtual frame state, transitioning held keys and mouse to current."""
        self.previous_keys = self.current_keys.copy()
        self.current_keys = self._held_keys.copy()
        self._update_typematic_repeat(now)

        self.mouse_position = self._virtual_mouse_pos

        self.mouse_just_pressed = self._virtual_mouse_pressed and not self.mouse_pressed
        self.mouse_pressed = self._virtual_mouse_pressed

        self.mouse_right_just_pressed = self._virtual_mouse_right_pressed and not self.mouse_right_pressed
        self.mouse_right_pressed = self._virtual_mouse_right_pressed
