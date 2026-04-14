def clear_console():
    return "\033[2J"


def move_cursor(column: int, line: int):
    return f"\033[{line + 1};{column + 1}H"


def hide_cursor():
    return "\033[?25l"


def show_cursor():
    return "\033[?25h"


def fg_color(r: int, g: int, b: int):
    return f"\033[38;2;{r};{g};{b}m"


def bg_color(r: int, g: int, b: int):
    return f"\033[48;2;{r};{g};{b}m"


def reset_color():
    return "\033[0m"
