from dataclasses import dataclass


def pos(x: int, y: int) -> Position:
    return Position(x, y)


def size(columns: int, lines: int) -> Size:
    return Size(columns, lines)


@dataclass
class Position:
    x: int
    y: int


@dataclass
class Size:
    columns: int
    lines: int
