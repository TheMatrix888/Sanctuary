"""
Input handling subsystem for Sanctuary.
Provides platform-agnostic key enumeration, discrete press detection,
and stateful keystroke tracking.
"""
import ctypes
from abc import ABC, abstractmethod
from ctypes import wintypes
from enum import StrEnum

from sanctuary.core.terminal import WindowsTerminal


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


class InputHandler(ABC):
    """
    Abstract base input handler providing frame-bound key tracking and state queries.
    Maintains current and previous frame key snapshots for idempotent lookups.
    """

    def __init__(self) -> None:
        self.current_keys: set[Key] = set()
        self.previous_keys: set[Key] = set()

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

    def is_pressed(self, key: Key | str) -> bool:
        """Returns True if the key is currently held down in this frame."""
        normalized = self._normalize_key(key)
        return normalized in self.current_keys if normalized else False

    def just_pressed(self, key: Key | str) -> bool:
        """Returns True only on the initial frame the key was pressed down."""
        normalized = self._normalize_key(key)
        if not normalized:
            return False
        return (normalized in self.current_keys) and (normalized not in self.previous_keys)


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
    }

    def __init__(self, terminal: WindowsTerminal) -> None:
        super().__init__()
        self.terminal = terminal
        self._user32 = ctypes.windll.user32
        self._user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self._user32.GetAsyncKeyState.restype = wintypes.SHORT
        self._user32.GetForegroundWindow.argtypes = []
        self._user32.GetForegroundWindow.restype = wintypes.HWND

    def update(self) -> None:
        """Captures hardware keystroke state snapshot for the current frame."""
        self.previous_keys = self.current_keys.copy()
        self.current_keys = set()

        # Ignore input when the terminal window is not in foreground focus
        if self._user32.GetForegroundWindow() != self.terminal.hwnd:
            return

        for key, vk_code in self.KEY_MAP.items():
            if self._user32.GetAsyncKeyState(vk_code) & 0x8000:
                self.current_keys.add(key)


class VirtualInputHandler(InputHandler):
    """
    Headless in-memory input driver for automated testing and CI pipelines.
    Allows programmatic simulation of key presses and releases without hardware.
    """

    def __init__(self) -> None:
        super().__init__()
        self._held_keys: set[Key] = set()

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

    def update(self) -> None:
        """Advances the virtual frame state, transitioning held keys to current."""
        self.previous_keys = self.current_keys.copy()
        self.current_keys = self._held_keys.copy()
