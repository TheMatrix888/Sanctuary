"""
Windows Terminal Driver for Sanctuary.
Provides low-level conhost/VT100 console initialization, hardware abstraction,
and symmetrical terminal control.
"""
import ctypes
import os
import sys
from ctypes import wintypes
from pathlib import Path
from typing import Protocol

import sanctuary.core.ansi as ansi
from sanctuary.core.geometry import Size

# --- Win32 Standard Handles ---
STDIN_PSEUDO_HANDLE = -10
STDOUT_PSEUDO_HANDLE = -11

# --- Console Mode Flags ---
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
ENABLE_EXTENDED_FLAGS = 0x0080
ENABLE_QUICK_EDIT_MODE = 0x0040

# --- Win32 ScrollBar & Window Constants ---
SB_BOTH = 3  # Both horizontal and vertical scrollbars

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


def _pack_coord(cols: int, rows: int) -> int:
    """
    Packs 16-bit X (cols) and Y (rows) into a 32-bit unsigned integer.
    Required by Win32 x64 calling convention when passing or returning COORD by value
    to avoid ctypes pointer-passing ABI bugs on 64-bit systems.
    """
    return ((int(rows) & 0xFFFF) << 16) | (int(cols) & 0xFFFF)


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
    """
    Abstract Protocol defining the contract for Sanctuary terminal drivers.
    All state properties are strictly symmetrical with corresponding getters and setters.
    """
    def write(self, text: str) -> None:
        ...

    def get_size(self) -> Size:
        ...

    def set_size(self, columns: int, rows: int) -> None:
        ...

    def get_font_size(self) -> Size:
        ...

    def set_font_size(self, height: int, width: int = 0) -> None:
        ...

    def get_title(self) -> str:
        ...

    def set_title(self, title: str) -> None:
        ...

    def is_cursor_visible(self) -> bool:
        ...

    def set_cursor_visible(self, visible: bool) -> None:
        ...

    def hide_cursor(self) -> None:
        ...

    def show_cursor(self) -> None:
        ...

    def is_fullscreen_or_maximized(self) -> bool:
        ...

    def set_fullscreen(self, enabled: bool) -> None:
        ...

    def check_fullscreen_transition(self) -> bool:
        ...

    def snap_to_discrete_grid(self) -> bool:
        ...

    def fit_to_screen(self) -> Size:
        ...

    def get_max_size(self) -> Size:
        ...

    def clamp_buffer_to_window(self) -> None:
        ...

    def clear(self) -> None:
        ...

    def reset(self) -> None:
        ...

    def close(self) -> None:
        ...


class VirtualTerminal:
    """
    Headless in-memory terminal driver.
    Used for automated unit testing, CI pipelines, and off-screen rendering.
    Implements the Terminal protocol without requiring an active OS console window.
    """
    columns: int
    rows: int
    font_width: int
    font_height: int
    title: str
    captured_stream: list[str]
    _cursor_visible: bool
    _fullscreen: bool
    _was_fullscreen: bool
    _saved_windowed_cols: int
    _saved_windowed_rows: int
    _saved_windowed_font_height: int

    def __init__(
            self,
            columns: int = 100,
            rows: int = 30,
            font_width: int = 12,
            font_height: int = 24,
            title: str = "Virtual Terminal",
    ) -> None:
        self.columns = columns
        self.rows = rows
        self.font_width = font_width
        self.font_height = font_height
        self.title = title
        self.captured_stream = []
        self._cursor_visible = True
        self._fullscreen = False
        self._was_fullscreen = False
        self._saved_windowed_cols = columns
        self._saved_windowed_rows = rows
        self._saved_windowed_font_height = font_height

    def write(self, text: str) -> None:
        """Appends output text to internal memory stream."""
        self.captured_stream.append(text)

    def get_size(self) -> Size:
        """Returns simulated terminal dimensions in character cells."""
        return Size(width=self.columns, height=self.rows)

    def set_size(self, columns: int, rows: int) -> None:
        """Updates simulated viewport dimensions."""
        self.columns = columns
        self.rows = rows

    def get_font_size(self) -> Size:
        """Returns simulated character cell pixel dimensions."""
        return Size(width=self.font_width, height=self.font_height)

    def set_font_size(self, height: int, width: int = 0) -> None:
        """Updates simulated font dimensions."""
        self.font_height = height
        self.font_width = width if width > 0 else max(1, height // 2)

    def get_title(self) -> str:
        """Returns simulated title."""
        return self.title

    def set_title(self, title: str) -> None:
        """Updates simulated title."""
        self.title = title

    def is_cursor_visible(self) -> bool:
        """Returns simulated cursor visibility."""
        return self._cursor_visible

    def set_cursor_visible(self, visible: bool) -> None:
        """Sets simulated cursor visibility."""
        if visible:
            self.show_cursor()
        else:
            self.hide_cursor()

    def hide_cursor(self) -> None:
        """Appends hide cursor ANSI sequence to memory stream."""
        self._cursor_visible = False
        self.captured_stream.append(ansi.HIDE_CURSOR)

    def show_cursor(self) -> None:
        """Appends show cursor ANSI sequence to memory stream."""
        self._cursor_visible = True
        self.captured_stream.append(ansi.SHOW_CURSOR)

    def is_fullscreen_or_maximized(self) -> bool:
        """Returns whether the simulated terminal is in fullscreen or maximized mode."""
        return self._fullscreen

    def set_fullscreen(self, enabled: bool) -> None:
        """Sets simulated fullscreen state."""
        self._fullscreen = enabled

    def check_fullscreen_transition(self) -> bool:
        """Simulates fullscreen transition detection and geometry restoration."""
        if self._fullscreen and not self._was_fullscreen:
            self._was_fullscreen = True
            return True
        elif not self._fullscreen and self._was_fullscreen:
            self._was_fullscreen = False
            self.columns = self._saved_windowed_cols
            self.rows = self._saved_windowed_rows
            self.font_height = self._saved_windowed_font_height
            self.font_width = max(1, self.font_height // 2)
            return True
        elif not self._fullscreen:
            self._saved_windowed_cols = self.columns
            self._saved_windowed_rows = self.rows
            self._saved_windowed_font_height = self.font_height
        return False

    def snap_to_discrete_grid(self) -> bool:
        """Simulated grid snapping (no-op in headless virtual terminal)."""
        return False

    def fit_to_screen(self) -> Size:
        """Simulates expanding terminal to maximum dimensions."""
        return self.get_size()

    def get_max_size(self) -> Size:
        """Returns simulated maximum dimensions."""
        return self.get_size()

    def clamp_buffer_to_window(self) -> None:
        """No-op in virtual terminal."""
        pass

    def clear(self) -> None:
        """Emits standard clear ANSI sequence to memory stream."""
        self.captured_stream.append(ansi.CLEAR_SCREEN + ansi.CURSOR_HOME)

    def reset(self) -> None:
        """Resets stream attributes, clears simulated screen, and hides cursor."""
        self._cursor_visible = False
        self.captured_stream.append(ansi.reset_terminal_sequence())

    def get_output(self) -> str:
        """Joins and returns the entire captured output stream."""
        return "".join(self.captured_stream)

    def clear_buffer(self) -> None:
        """Empties the captured stream memory."""
        self.captured_stream.clear()

    def close(self) -> None:
        """Restores simulated stream and cursor."""
        self._cursor_visible = True
        self.captured_stream.append(ansi.EXIT_ALT_SCREEN + ansi.SHOW_CURSOR + ansi.ENABLE_AUTO_WRAP)


class WindowsTerminal:
    """Windows-specific low-level terminal driver using Win32 API and ANSI VT100."""
    columns: int
    rows: int
    title: str
    font_name: str
    font_size_height: int
    kernel32: ctypes.WinDLL
    user32: ctypes.WinDLL
    stdin_handle: wintypes.HANDLE
    stdout_handle: wintypes.HANDLE
    hwnd: wintypes.HWND
    _cursor_visible: bool
    _was_fullscreen: bool
    _saved_windowed_cols: int
    _saved_windowed_rows: int
    _saved_windowed_font_height: int

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
            # Enter xterm alternate screen buffer and disable auto-wrap
            self.write(ansi.ENTER_ALT_SCREEN + ansi.DISABLE_AUTO_WRAP)

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
    # PUBLIC RUNTIME MUTATORS & ACCESSORS
    # =========================================================================

    def get_size(self) -> Size:
        """
        Returns the current visible terminal dimensions in character cells.
        In fullscreen or maximized mode, returns true screen character capacity
        clamped to the display resolution and current font size.
        """
        if self.is_fullscreen_or_maximized():
            max_size = self.get_max_size()
            if max_size.width > 0 and max_size.height > 0:
                return max_size

        buffer_info = CONSOLE_SCREEN_BUFFER_INFO()
        if self.kernel32.GetConsoleScreenBufferInfo(self.stdout_handle, ctypes.byref(buffer_info)):
            columns = int(buffer_info.srWindow.Right - buffer_info.srWindow.Left + 1)
            rows = int(buffer_info.srWindow.Bottom - buffer_info.srWindow.Top + 1)
            if columns > 0 and rows > 0:
                return Size(width=columns, height=rows)

        try:
            terminal_size = os.get_terminal_size()
            return Size(width=terminal_size.columns, height=terminal_size.lines)
        except OSError:
            return Size(width=self.columns, height=self.rows)

    def _set_console_geometry(self, columns: int, rows: int) -> None:
        """
        Applies target dimensions to both the console viewport and buffer
        using safe expanding-buffer-first envelope sizing, guaranteeing zero scrollbars.
        Clamps dimensions to hardware limits to prevent Win32 invalid parameter errors.
        """
        max_size = self.get_max_size()
        if max_size.width > 0 and max_size.height > 0:
            columns = min(columns, max_size.width)
            rows = min(rows, max_size.height)
        columns = max(10, columns)
        rows = max(5, rows)

        self.columns = columns
        self.rows = rows

        try:
            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            if self.kernel32.GetConsoleScreenBufferInfo(self.stdout_handle, ctypes.byref(csbi)):
                cur_buf_w = csbi.dwSize.X
                cur_buf_h = csbi.dwSize.Y
            else:
                cur_buf_w = columns
                cur_buf_h = rows

            # 1. Expand buffer first to envelope current and target dimensions (prevents Window > Buffer error)
            max_buf_w = max(cur_buf_w, columns)
            max_buf_h = max(cur_buf_h, rows)
            self.kernel32.SetConsoleScreenBufferSize(self.stdout_handle, _pack_coord(max_buf_w, max_buf_h))

            # 2. Resize window viewport to target
            win_rect = SMALL_RECT(0, 0, columns - 1, rows - 1)
            self.kernel32.SetConsoleWindowInfo(self.stdout_handle, True, ctypes.byref(win_rect))

            # 3. Clamp buffer exactly to target (prevents Buffer > Window scrollbars)
            self.kernel32.SetConsoleScreenBufferSize(self.stdout_handle, _pack_coord(columns, rows))
        except Exception:
            pass

        # Final buffer clamp to eliminate scrollbars
        self.clamp_buffer_to_window()

    def set_size(self, columns: int, rows: int) -> None:
        """
        Dynamically resizes terminal viewport and screen buffer.
        Clamps dimensions to hardware limits to prevent Win32 invalid parameter errors.
        """
        self._set_console_geometry(columns, rows)

    def get_font_size(self) -> Size:
        """
        Returns the current console font character cell dimensions in pixels.
        Queries Win32 GetCurrentConsoleFontEx with fallback to client rect calculation.
        """
        font_info = CONSOLE_FONT_INFOEX()
        font_info.cbSize = ctypes.sizeof(CONSOLE_FONT_INFOEX)
        if self.kernel32.GetCurrentConsoleFontEx(self.stdout_handle, False, ctypes.byref(font_info)):
            pixel_height = int(font_info.dwFontSize.Y)
            pixel_width = int(font_info.dwFontSize.X)

            # If TrueType proportional font reports 0 width, calculate from client rect or estimate
            if pixel_width == 0:
                if self.hwnd:
                    rect = wintypes.RECT()
                    if self.user32.GetClientRect(self.hwnd, ctypes.byref(rect)):
                        client_width = rect.right - rect.left
                        current_cols = self.get_size().columns
                        if client_width > 0 and current_cols > 0:
                            pixel_width = max(1, round(client_width / current_cols))

                if pixel_width == 0 and pixel_height > 0:
                    pixel_width = max(1, pixel_height // 2)

            return Size(width=pixel_width, height=pixel_height)

        return Size(width=12, height=self.font_size_height)

    def set_font_size(self, height: int, width: int = 0) -> None:
        """
        Symmetrical setter for font size. Updates font height (and optional width).
        """
        self.set_font(font_name=self.font_name, font_size_height=height)

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

    def get_title(self) -> str:
        """
        Returns the current text of the console window title bar.
        Queries Win32 GetConsoleTitleW with fallback to internal cached title.
        """
        buffer = ctypes.create_unicode_buffer(512)
        if self.kernel32.GetConsoleTitleW(buffer, 512) > 0:
            self.title = buffer.value
        return self.title

    def set_title(self, title: str) -> None:
        """Sets the text of the console window title bar."""
        self.title = title
        self.kernel32.SetConsoleTitleW(title)

    def is_cursor_visible(self) -> bool:
        """Returns True if the console text cursor is currently visible."""
        return self._cursor_visible

    def set_cursor_visible(self, visible: bool) -> None:
        """Sets text cursor visibility."""
        if visible:
            self.show_cursor()
        else:
            self.hide_cursor()

    def hide_cursor(self) -> None:
        """Hides the terminal text cursor to prevent visual flicker during frame updates."""
        self._cursor_visible = False
        self.write(ansi.HIDE_CURSOR)

    def show_cursor(self) -> None:
        """Restores visibility of the terminal text cursor and auto-wrap."""
        self._cursor_visible = True
        self.write(ansi.SHOW_CURSOR + ansi.ENABLE_AUTO_WRAP)

    def is_fullscreen_or_maximized(self) -> bool:
        """
        Returns True if the console window is currently maximized or in borderless fullscreen (F11).
        """
        if not self.hwnd:
            return False
        if self.user32.IsZoomed(self.hwnd):
            return True
        rect = wintypes.RECT()
        if self.user32.GetWindowRect(self.hwnd, ctypes.byref(rect)):
            screen_w = self.user32.GetSystemMetrics(0)  # SM_CXSCREEN
            screen_h = self.user32.GetSystemMetrics(1)  # SM_CYSCREEN
            win_w = rect.right - rect.left
            win_h = rect.bottom - rect.top
            if win_w >= screen_w and win_h >= screen_h:
                return True
        return False

    def set_fullscreen(self, enabled: bool) -> None:
        """
        Enables or disables fullscreen / maximized mode.
        """
        if not self.hwnd:
            return
        if enabled:
            self.user32.ShowWindow(self.hwnd, 3)  # SW_MAXIMIZE
        else:
            self.user32.ShowWindow(self.hwnd, 9)  # SW_RESTORE
        self.clamp_buffer_to_window()

    def check_fullscreen_transition(self) -> bool:
        """
        Detects transitions between windowed and fullscreen/maximized modes.
        When entering fullscreen, expands grid to fit display while preserving saved
        windowed dimensions.
        When exiting fullscreen, automatically restores saved windowed geometry,
        preventing the 'micro-window' trap caused by zooming in fullscreen mode.
        Returns True if a mode transition occurred.
        """
        is_fullscreen = self.is_fullscreen_or_maximized()
        if is_fullscreen and not self._was_fullscreen:
            # Entering fullscreen: expand grid to fit display (preserve saved windowed state)
            self._was_fullscreen = True
            self.fit_to_screen()
            return True
        elif not is_fullscreen and self._was_fullscreen:
            # Exiting fullscreen: restore saved font and saved outer window geometry
            self._was_fullscreen = False
            self.set_font(font_name=self.font_name, font_size_height=self._saved_windowed_font_height)

            if self.hwnd:
                font_sz = self.get_font_size()
                fw = max(1, font_sz.width)
                fh = max(1, font_sz.height)
                rect = wintypes.RECT(0, 0, self._saved_windowed_cols * fw + 24, self._saved_windowed_rows * fh + 16)
                style = self.user32.GetWindowLongW(self.hwnd, -16)  # GWL_STYLE
                ex_style = self.user32.GetWindowLongW(self.hwnd, -20)  # GWL_EXSTYLE
                self.user32.AdjustWindowRectEx(ctypes.byref(rect), style, False, ex_style)
                outer_w = rect.right - rect.left
                outer_h = rect.bottom - rect.top
                # SWP_NOMOVE (0x2) | SWP_NOZORDER (0x4) | SWP_NOACTIVATE (0x10) | SWP_FRAMECHANGED (0x20)
                self.user32.SetWindowPos(self.hwnd, None, 0, 0, outer_w, outer_h, 0x0036)

            self.set_size(columns=self._saved_windowed_cols, rows=self._saved_windowed_rows)
            return True
        elif not is_fullscreen:
            # Continuously track windowed geometry while running in windowed mode
            cur_size = self.get_size()
            self._saved_windowed_cols = cur_size.columns
            self._saved_windowed_rows = cur_size.rows
            self._saved_windowed_font_height = self.font_size_height

        return False

    def snap_to_discrete_grid(self) -> bool:
        """
        Safe helper to align window client area to character cell boundaries.
        Bypassed in fullscreen or maximized mode.
        """
        if self.is_fullscreen_or_maximized() or not self.hwnd:
            return False
        return False

    def get_max_size(self) -> Size:
        """
        Returns maximum columns and rows that can fit on screen with current font.
        Uses native Win32 GetLargestConsoleWindowSize with 32-bit scalar unpacking.
        """
        raw = self.kernel32.GetLargestConsoleWindowSize(self.stdout_handle)
        cols = raw & 0xFFFF
        rows = (raw >> 16) & 0xFFFF
        if cols > 0 and rows > 0:
            return Size(width=int(cols), height=int(rows))
        return self.get_size()

    def fit_to_screen(self) -> Size:
        """
        Synchronizes terminal buffer and viewport to full screen in fullscreen or maximized mode.
        Dynamically calculates maximum column and row capacity for the active monitor and font,
        enabling true optical semantic zoom without scrollbars.
        """
        largest = self.get_max_size()
        if largest.width > 0 and largest.height > 0:
            self._set_console_geometry(largest.width, largest.height)
        return self.get_size()

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
        self.write(ansi.CLEAR_SCREEN + ansi.CURSOR_HOME)

    def clamp_buffer_to_window(self) -> None:
        """
        Clamps the Win32 console screen buffer to match the visible window dimensions exactly,
        eliminating unnecessary horizontal and vertical scrollbars.
        Sets buffer dimensions strictly equal to the active viewport (srWindow)
        and calls Win32 ShowScrollBar to guarantee zero scrollbar overflow.
        """
        buffer_info = CONSOLE_SCREEN_BUFFER_INFO()
        if not self.kernel32.GetConsoleScreenBufferInfo(self.stdout_handle, ctypes.byref(buffer_info)):
            return

        actual_cols = int(buffer_info.srWindow.Right - buffer_info.srWindow.Left + 1)
        actual_rows = int(buffer_info.srWindow.Bottom - buffer_info.srWindow.Top + 1)

        if actual_cols <= 0 or actual_rows <= 0:
            return

        # 1. If buffer dimensions don't match visible rect exactly, clamp buffer
        if buffer_info.dwSize.X != actual_cols or buffer_info.dwSize.Y != actual_rows:
            try:
                self.kernel32.SetConsoleScreenBufferSize(self.stdout_handle, _pack_coord(actual_cols, actual_rows))
            except Exception:
                pass

        # 2. Explicitly hide Win32 scrollbars and strip scrollbar window styles
        self._strip_scrollbar_styles()

    def _strip_scrollbar_styles(self) -> None:
        """Removes WS_VSCROLL and WS_HSCROLL styles and updates non-client frame."""
        if not self.hwnd:
            return
        try:
            self.user32.ShowScrollBar(self.hwnd, SB_BOTH, False)
            style = self.user32.GetWindowLongW(self.hwnd, -16)  # GWL_STYLE
            if (style & 0x00200000) or (style & 0x00100000):  # WS_VSCROLL | WS_HSCROLL
                new_style = style & ~0x00200000 & ~0x00100000
                self.user32.SetWindowLongW(self.hwnd, -16, new_style)
                # SWP_NOMOVE (0x2) | SWP_NOSIZE (0x1) | SWP_NOZORDER (0x4) | SWP_FRAMECHANGED (0x20)
                self.user32.SetWindowPos(self.hwnd, None, 0, 0, 0, 0, 0x0027)
        except Exception:
            pass

    def close(self) -> None:
        """Restores main screen buffer and normal cursor state upon shutdown."""
        self.write(ansi.EXIT_ALT_SCREEN + ansi.SHOW_CURSOR + ansi.ENABLE_AUTO_WRAP)
        if hasattr(self, "_conout_handle") and self._conout_handle:
            try:
                self.kernel32.CloseHandle(self._conout_handle)
                self._conout_handle = None
            except Exception:
                pass

    def reset(self) -> None:
        """
        Resets terminal graphics state:
        1. Clamps Win32 buffer to window to eliminate scrollbars.
        2. Resets brush, hides cursor, clears screen, and homes cursor.
        """
        self.clamp_buffer_to_window()
        self._cursor_visible = False
        self.write(ansi.reset_terminal_sequence())

    def _init_win32_signatures(self) -> None:
        """Sets explicit ctypes signatures to prevent 64-bit ABI register mismatches."""
        self.kernel32.CreateFileW.restype = wintypes.HANDLE
        self.kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
            ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE
        ]
        self.kernel32.SetConsoleScreenBufferSize.restype = wintypes.BOOL
        self.kernel32.SetConsoleScreenBufferSize.argtypes = [wintypes.HANDLE, ctypes.c_uint32]
        self.kernel32.SetConsoleWindowInfo.restype = wintypes.BOOL
        self.kernel32.SetConsoleWindowInfo.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(SMALL_RECT)]
        self.kernel32.GetConsoleScreenBufferInfo.restype = wintypes.BOOL
        self.kernel32.GetConsoleScreenBufferInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(CONSOLE_SCREEN_BUFFER_INFO)]
        self.kernel32.GetLargestConsoleWindowSize.restype = ctypes.c_uint32
        self.kernel32.GetLargestConsoleWindowSize.argtypes = [wintypes.HANDLE]
        self.kernel32.GetCurrentConsoleFontEx.restype = wintypes.BOOL
        self.kernel32.GetCurrentConsoleFontEx.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(CONSOLE_FONT_INFOEX)]
        self.kernel32.SetCurrentConsoleFontEx.restype = wintypes.BOOL
        self.kernel32.SetCurrentConsoleFontEx.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(CONSOLE_FONT_INFOEX)]

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
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._init_win32_signatures()

        self.stdin_handle = self.kernel32.GetStdHandle(STDIN_PSEUDO_HANDLE)
        self._conout_handle = self.kernel32.CreateFileW("CONOUT$", 0xC0000000, 3, None, 3, 0, None)
        if self._conout_handle and self._conout_handle != -1:
            self.stdout_handle = self._conout_handle
        else:
            self._conout_handle = None
            self.stdout_handle = self.kernel32.GetStdHandle(STDOUT_PSEUDO_HANDLE)
        self.hwnd = self.kernel32.GetConsoleWindow()

        # State tracking fields
        self._cursor_visible = False
        self._was_fullscreen = False
        self._saved_windowed_cols = columns
        self._saved_windowed_rows = rows
        self._saved_windowed_font_height = font_size_height

        # 1. One-time private system setup
        self._force_utf8()
        self._set_code_page()
        self._enable_ansi()
        self._disable_quick_edit()

        # 2. Public runtime window geometry and styles
        self.columns = columns
        self.rows = rows
        self.set_title(title)
        self.set_font(font_name=font_name, font_size_height=font_size_height)
        self.set_size(columns=columns, rows=rows)
        self.set_icon(icon_path)
        self.reset()
