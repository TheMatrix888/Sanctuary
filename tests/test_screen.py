"""
Unit tests for Screen lifecycle, buffer resizing, and window minimization/restoration transitions.
"""
from sanctuary.core.config import DisplayConfig
from sanctuary.core.geometry import Rect, Size
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.terminal import VirtualTerminal


def test_screen_restore_from_minimize_hides_cursor() -> None:
    terminal = VirtualTerminal()
    display = DisplayConfig(columns=80, rows=25)
    screen = Screen(terminal, display)

    # Initial state: cursor hidden by Screen.reset()
    assert terminal.is_cursor_visible() is False

    # Simulate external event (or Conhost focus restore) revealing cursor
    terminal.show_cursor()
    assert terminal.is_cursor_visible() is True

    # 1. Window is minimized to taskbar
    terminal.simulate_minimize()
    assert screen.check_resize() is False

    # 2. Window is restored from taskbar
    terminal.simulate_restore()

    # check_resize must catch the restore transition
    assert screen.check_resize() is True
    assert screen._force_full_redraw is True

    # Hardware cursor must be immediately suppressed
    assert terminal.is_cursor_visible() is False

    # Subsequent frame: transition flag consumed, returns False
    assert screen.check_resize() is False


def test_screen_fill_rect_and_clipping() -> None:
    terminal = VirtualTerminal()
    display = DisplayConfig(columns=40, rows=20)
    screen = Screen(terminal, display)

    rect = Rect(5, 5, 4, 3)
    fill_color = Color(200, 50, 50)
    screen.fill_rect(rect, char="*", fg_color=fill_color)

    for point in rect:
        cell = screen.back_buffer.cells[point.y][point.x]
        assert cell.char == "*"
        assert cell.fg_color == fill_color

    # Boundary clipping test without throwing index errors
    clipped_rect = Rect(35, 18, 10, 10)
    screen.fill_rect(clipped_rect, char="@")
    assert screen.back_buffer.cells[19][39].char == "@"
