"""
Windows Terminal Driver for Sanctuary.
Provides low-level conhost/VT100 console initialization and hardware abstraction.
"""
import ctypes
import os
import sys
from ctypes import wintypes
from pathlib import Path
from typing import Protocol

from sanctuary.core.geometry import Size

# --- Win32 Standard Handles ---
STDIN_PSEUDO_HANDLE = -10
STDOUT_PSEUDO_HANDLE = -11

# --- Console Mode Flags ---
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
ENABLE_EXTENDED_FLAGS = 0x0080
ENABLE_QUICK_EDIT_MODE = 0x0040

# --- Win32 Window Messages & Resource Loading (Icon API) ---
IMAGE_ICON = 1  # 1 = Load an icon resource (.ico), not bitmap or cursor
LR_LOADFROMFILE = 0x0010  # Load resource from standalone file path rather than embedded DLL/EXE
WM_SETICON = 0x0080  # Windows Message: "associate a new large or small icon with a window"
ICON_SMALL = 0  # 16x16 icon for window title bar and system tray
ICON_BIG = 1  # 32x32 icon for Alt+Tab task switcher

# --- Win32 Window Class Long Pointers (Taskbar Icon API) ---
GCLP_HICON = -14  # Window Class offset: large icon for Windows Taskbar grouping
GCLP_HICONSM = -34  # Window Class offset: small icon for Windows Taskbar grouping


class COORD(ctypes.Structure):
    _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]


class SMALL_RECT(ctypes.Structure):
    _fields_ = [
        ("Left", wintypes.SHORT),
        ("Top", wintypes.SHORT),
        ("Right", wintypes.SHORT),
        ("Bottom", wintypes.SHORT),
    ]


class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [
        ("dwSize", COORD),
        ("dwCursorPosition", COORD),
        ("wAttributes", wintypes.WORD),
        ("srWindow", SMALL_RECT),
        ("dwMaximumWindowSize", COORD),
    ]


class CONSOLE_FONT_INFOEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.ULONG),
        ("nFont", wintypes.DWORD),
        ("dwFontSize", COORD),
        ("FontFamily", wintypes.UINT),
        ("FontWeight", wintypes.UINT),
        ("FaceName", wintypes.WCHAR * 32),
    ]


class Terminal(Protocol):
    def write(self, text: str) -> None:
        ...

    def set_size(self, columns: int, rows: int) -> None:
        ...

    def get_size(self) -> Size:
        ...

    def set_title(self, title: str) -> None:
        ...

    def clear(self) -> None:
        ...

    def hide_cursor(self) -> None:
        ...

    def show_cursor(self) -> None:
        ...


class VirtualTerminal:
    """
    Headless in-memory terminal driver.
    Used for automated unit testing, CI pipelines, and off-screen rendering.
    Implements the Terminal protocol without requiring an active OS console window.
    """

    def __init__(
            self,
            columns: int = 100,
            rows: int = 30,
            title: str = "Virtual Terminal",
    ) -> None:
        self.columns = columns
        self.rows = rows
        self.title = title
        self.captured_stream: list[str] = []

    def write(self, text: str) -> None:
        """Appends output text to internal memory stream."""
        self.captured_stream.append(text)

    def set_size(self, columns: int, rows: int) -> None:
        """Updates simulated viewport dimensions."""
        self.columns = columns
        self.rows = rows

    def get_size(self) -> Size:
        """Returns simulated terminal dimensions."""
        return Size(width=self.columns, height=self.rows)

    def set_title(self, title: str) -> None:
        """Updates simulated title."""
        self.title = title

    def clear(self) -> None:
        """Emits standard clear ANSI sequence to memory stream."""
        self.captured_stream.append("\033[2J\033[H")

    def hide_cursor(self) -> None:
        """Appends hide cursor ANSI sequence to memory stream."""
        self.captured_stream.append("\033[?25l")

    def show_cursor(self) -> None:
        """Appends show cursor ANSI sequence to memory stream."""
        self.captured_stream.append("\033[?25h")

    def get_output(self) -> str:
        """Joins and returns the entire captured output stream."""
        return "".join(self.captured_stream)

    def clear_buffer(self) -> None:
        """Empties the captured stream memory."""
        self.captured_stream.clear()


class WindowsTerminal:
    """Windows-specific low-level terminal driver using Win32 API and ANSI VT100."""

    # =========================================================================
    # PRIVATE INITIALIZATION METHODS (One-time startup configuration)
    # =========================================================================

    @staticmethod
    def _force_utf8() -> None:
        """Reconfigures standard Python I/O streams to UTF-8 encoding."""
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")

    def _set_code_page(self) -> None:
        """Sets Windows console input and output code pages to UTF-8 (CP 65001)."""
        self.kernel32.SetConsoleOutputCP(65001)
        self.kernel32.SetConsoleCP(65001)

    def _enable_ansi(self) -> None:
        """Enables hardware VT100 ANSI escape sequence parsing in Windows 10 conhost."""
        stdout_mode = wintypes.DWORD()
        if self.kernel32.GetConsoleMode(self.stdout_handle, ctypes.byref(stdout_mode)):
            new_mode = stdout_mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            self.kernel32.SetConsoleMode(self.stdout_handle, new_mode)
            # Disable DEC Auto-Wrap Mode (DECAWM) to prevent bottom-right cell autoscroll
            sys.stdout.write("\033[?7l")
            sys.stdout.flush()

    def _disable_quick_edit(self) -> None:
        """
        Disables QuickEdit mode.
        Prevents accidental mouse clicks from suspending the application execution thread.
        """
        stdin_mode = wintypes.DWORD()
        if self.kernel32.GetConsoleMode(self.stdin_handle, ctypes.byref(stdin_mode)):
            new_mode = (stdin_mode.value | ENABLE_EXTENDED_FLAGS) & ~ENABLE_QUICK_EDIT_MODE
            self.kernel32.SetConsoleMode(self.stdin_handle, new_mode)

    # =========================================================================
    # PUBLIC RUNTIME MUTATORS (Callable anytime during application runtime)
    # =========================================================================

    def set_font(
            self,
            font_name: str = "Cascadia Mono",
            font_size_height: int = 24,
            bold: bool = False,
    ) -> None:
        """
        Dynamically changes console font and height via Win32 API.
        Guarantees scalable TrueType vector rendering over microscopic raster fonts.
        """
        self.font_name = font_name
        self.font_size_height = font_size_height

        font_info = CONSOLE_FONT_INFOEX()
        font_info.cbSize = ctypes.sizeof(CONSOLE_FONT_INFOEX)
        font_info.nFont = 0
        font_info.dwFontSize.X = 0  # 0 = automatic proportional width calculation
        font_info.dwFontSize.Y = font_size_height
        font_info.FontFamily = 54  # TMPF_VECTOR | FF_MODERN (Scalable monospaced TrueType)
        font_info.FontWeight = 700 if bold else 400
        font_info.FaceName = font_name

        self.kernel32.SetCurrentConsoleFontEx(self.stdout_handle, False, ctypes.byref(font_info))

    def set_size(self, columns: int, rows: int) -> None:
        """
        Dynamically resizes terminal viewport and screen buffer.
        Synchronizes both Win32 buffer dimensions and VT100 ANSI viewport,
        clamping the screen buffer to eliminate conhost scrollbars.
        """
        self.columns = columns
        self.rows = rows

        try:
            # Temporarily shrink window to allow buffer resizing
            min_rect = SMALL_RECT(0, 0, 1, 1)
            self.kernel32.SetConsoleWindowInfo(self.stdout_handle, True, ctypes.byref(min_rect))
            # Set buffer dimensions exactly
            self.kernel32.SetConsoleScreenBufferSize(self.stdout_handle, COORD(columns, rows))
            # Set window dimensions to match
            win_rect = SMALL_RECT(0, 0, columns - 1, rows - 1)
            self.kernel32.SetConsoleWindowInfo(self.stdout_handle, True, ctypes.byref(win_rect))
            # Final clamp to eliminate vertical scrollbar
            self.kernel32.SetConsoleScreenBufferSize(self.stdout_handle, COORD(columns, rows))
        except Exception:
            pass

        sys.stdout.write(f"\033[8;{rows};{columns}t")
        sys.stdout.flush()

    def get_size(self) -> Size:
        """
        Returns the current visible terminal dimensions in character cells.
        Queries native Win32 console buffer info with standard library fallback.
        """
        buffer_info = CONSOLE_SCREEN_BUFFER_INFO()
        if self.kernel32.GetConsoleScreenBufferInfo(self.stdout_handle, ctypes.byref(buffer_info)):
            columns = buffer_info.srWindow.Right - buffer_info.srWindow.Left + 1
            rows = buffer_info.srWindow.Bottom - buffer_info.srWindow.Top + 1
            return Size(width=int(columns), height=int(rows))

        try:
            terminal_size = os.get_terminal_size()
            return Size(width=terminal_size.columns, height=terminal_size.lines)
        except OSError:
            return Size(width=self.columns, height=self.rows)

    def get_max_size(self) -> Size:
        """
        Returns maximum columns and rows that can fit on screen with current font.
        Uses native Win32 GetLargestConsoleWindowSize.
        """
        self.kernel32.GetLargestConsoleWindowSize.restype = COORD
        self.kernel32.GetLargestConsoleWindowSize.argtypes = [wintypes.HANDLE]
        largest_dimensions = self.kernel32.GetLargestConsoleWindowSize(self.stdout_handle)
        if largest_dimensions.X > 0 and largest_dimensions.Y > 0:
            return Size(width=int(largest_dimensions.X), height=int(largest_dimensions.Y))
        return self.get_size()

    def fit_to_screen(self) -> Size:
        """
        Expands terminal viewport and buffer to maximum dimensions supported by monitor.
        """
        max_size = self.get_max_size()
        if max_size.width > 0 and max_size.height > 0:
            self.set_size(columns=max_size.width, rows=max_size.height)
        return self.get_size()

    def set_title(self, title: str) -> None:
        """Sets the text of the console window title bar."""
        self.title = title
        self.kernel32.SetConsoleTitleW(title)

    def set_icon(self, icon_relative_path: str = "resources/icons/shiro.ico") -> bool:
        """
        Applies a custom .ico icon to both the window frame and the Windows Taskbar.
        """
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            project_root = Path(getattr(sys, "_MEIPASS"))
        else:
            project_root = Path(__file__).resolve().parents[2]

        full_icon_path = str((project_root / icon_relative_path).resolve())
        if not Path(full_icon_path).exists():
            fallback_path = Path.cwd() / icon_relative_path
            if fallback_path.exists():
                full_icon_path = str(fallback_path.resolve())
            else:
                return False

        # Load both 16x16 (title bar) and 32x32 (Alt+Tab / Taskbar) resolutions
        small_icon_handle = self.user32.LoadImageW(
            None, full_icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE
        )
        large_icon_handle = self.user32.LoadImageW(
            None, full_icon_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE
        )

        # 1. Dispatch WM_SETICON to change title bar and Alt+Tab icons
        if small_icon_handle:
            self.user32.SendMessageW(self.hwnd, WM_SETICON, ICON_SMALL, small_icon_handle)
        if large_icon_handle:
            self.user32.SendMessageW(self.hwnd, WM_SETICON, ICON_BIG, large_icon_handle)

        # 2. Update Window Class pointers to force Windows Taskbar shell grouping to update
        try:
            set_class_long_ptr = getattr(self.user32, "SetClassLongPtrW", getattr(self.user32, "SetClassLongW", None))
            if set_class_long_ptr:
                if large_icon_handle:
                    set_class_long_ptr(self.hwnd, GCLP_HICON, large_icon_handle)
                if small_icon_handle:
                    set_class_long_ptr(self.hwnd, GCLP_HICONSM, small_icon_handle)
        except Exception:
            pass

        return True

    def write(self, text: str) -> None:
        """Fast direct text output to stdout stream with immediate buffer flush."""
        sys.stdout.write(text)
        sys.stdout.flush()

    def clear(self) -> None:
        """Clears screen and repositions cursor to home position (1;1)."""
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def hide_cursor(self) -> None:
        """Hides the terminal text cursor to prevent visual flicker during frame updates."""
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    def show_cursor(self) -> None:
        """Restores visibility of the terminal text cursor and auto-wrap."""
        sys.stdout.write("\033[?25h\033[?7h")
        sys.stdout.flush()

    # =========================================================================
    # CONSTRUCTOR
    # =========================================================================

    def __init__(
            self,
            columns: int = 120,
            rows: int = 30,
            title: str = "Sanctuary [Shiro]",
            font_name: str = "Cascadia Mono",
            font_size_height: int = 24,
            icon_path: str = "resources/icons/shiro.ico",
    ) -> None:
        # Win32 system handles and loaded kernel/user libraries
        self.kernel32 = ctypes.windll.kernel32
        self.user32 = ctypes.windll.user32
        self.stdin_handle = self.kernel32.GetStdHandle(STDIN_PSEUDO_HANDLE)
        self.stdout_handle = self.kernel32.GetStdHandle(STDOUT_PSEUDO_HANDLE)
        self.hwnd = self.kernel32.GetConsoleWindow()

        # 1. One-time private system setup
        self._force_utf8()
        self._set_code_page()
        self._enable_ansi()
        self._disable_quick_edit()

        # 2. Public runtime window geometry and styles
        self.columns = columns
        self.rows = rows
        self.set_size(columns=columns, rows=rows)
        self.set_title(title)
        self.set_font(font_name=font_name, font_size_height=font_size_height)
        self.set_icon(icon_path)
        self.hide_cursor()
        self.clear()
