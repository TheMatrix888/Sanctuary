import ctypes


class COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]


class SMALL_RECT(ctypes.Structure):
    _fields_ = [
        ("Left", ctypes.c_short),
        ("Top", ctypes.c_short),
        ("Right", ctypes.c_short),
        ("Bottom", ctypes.c_short)
    ]


class CONSOLE_FONT_INFOEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("nFont", ctypes.c_ulong),
        ("dwFontSize", COORD),
        ("FontFamily", ctypes.c_uint),
        ("FontWeight", ctypes.c_uint),
        ("FaceName", ctypes.c_wchar * 32)
    ]


class WindowsScreen:
    STD_OUTPUT_HANDLE = -11
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.user32 = ctypes.windll.user32

        self.handle = self.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE)
        self.hwnd = self.kernel32.GetConsoleWindow()

    def enable_ansi(self):
        mode = ctypes.c_ulong()
        self.kernel32.GetConsoleMode(self.handle, ctypes.byref(mode))
        self.kernel32.SetConsoleMode(
            self.handle,
            mode.value | self.ENABLE_VIRTUAL_TERMINAL_PROCESSING
        )

    def get_font_size(self):
        font = CONSOLE_FONT_INFOEX()
        font.cbSize = ctypes.sizeof(font)

        self.kernel32.GetCurrentConsoleFontEx(
            self.handle,
            False,
            ctypes.byref(font)
        )

        return font.dwFontSize.X, font.dwFontSize.Y

    def set_buffer_size(self, columns, lines):
        self.kernel32.SetConsoleScreenBufferSize(
            self.handle,
            COORD(columns, lines)
        )

    def set_window_size(self, columns, lines):
        rect = SMALL_RECT(0, 0, columns - 1, lines - 1)

        self.kernel32.SetConsoleWindowInfo(
            self.handle,
            True,
            ctypes.byref(rect)
        )

    def move(self, x, y, width, height):
        self.user32.MoveWindow(
            self.hwnd,
            x,
            y,
            width,
            height,
            True
        )

    def set_position_by_chars(self, x, y, columns, lines):
        font_width, font_height = self.get_font_size()

        width = columns * font_width
        height = lines * font_height

        self.move(x, y, width, height)

    def clear(self):
        ctypes.windll.kernel32.FillConsoleOutputCharacterW(
            self.handle,
            ctypes.c_wchar(" "),
            10000,
            COORD(0, 0),
            ctypes.byref(ctypes.c_ulong())
        )

    def set_title(self, title):
        ctypes.windll.kernel32.SetConsoleTitleW(title)
