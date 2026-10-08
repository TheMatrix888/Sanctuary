"""
ANSI VT100 / XTerm Escape Sequences for Sanctuary.
Provides atomic, type-safe string generators and constants for terminal control.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sanctuary.core.primitives import Color

# --- Text Formatting & Attributes ---
RESET_ATTRIBUTES = "\033[0m"

# --- Cursor Visibility & Auto-Wrap ---
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
DISABLE_AUTO_WRAP = "\033[?7l"
ENABLE_AUTO_WRAP = "\033[?7h"

# --- Alternate Screen Buffer (XTerm) ---
ENTER_ALT_SCREEN = "\033[?1049h"
EXIT_ALT_SCREEN = "\033[?1049l"

# --- Screen Clearing & Cursor Repositioning ---
CLEAR_SCREEN = "\033[2J"
CURSOR_HOME = "\033[H"


def move_cursor(x: int, y: int) -> str:
    """Emits 1-indexed VT100 Cursor Position (CUP) escape sequence."""
    return f"\033[{y + 1};{x + 1}H"


def fg_color(color: Color) -> str:
    """Emits ANSI 24-bit TrueColor foreground escape sequence."""
    r, g, b = color
    return f"\033[38;2;{r};{g};{b}m"


def bg_color(color: Color) -> str:
    """Emits ANSI 24-bit TrueColor background escape sequence."""
    r, g, b = color
    return f"\033[48;2;{r};{g};{b}m"


def resize_window(rows: int, columns: int) -> str:
    """Emits XTWINOPS resize console window escape sequence."""
    return f"\033[8;{rows};{columns}t"


def reset_terminal_sequence() -> str:
    """
    Composite reset sequence:
    1. Resets active brush and text attributes (RESET_ATTRIBUTES).
    2. Hides the text cursor to prevent visual flicker (HIDE_CURSOR).
    3. Clears the screen (CLEAR_SCREEN).
    4. Repositions cursor to home position 1;1 (CURSOR_HOME).
    """
    return f"{RESET_ATTRIBUTES}{HIDE_CURSOR}{CLEAR_SCREEN}{CURSOR_HOME}"
