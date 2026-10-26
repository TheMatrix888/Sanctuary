"""
Unit tests for geometric primitives, Point, Size, and Rect in sanctuary/core/geometry.py.
"""
import pytest
from sanctuary.core.geometry import Point, Size, Rect


class TestRect:
    def test_rect_properties(self) -> None:
        rect = Rect(10, 20, 30, 40)
        assert rect.x == 10
        assert rect.y == 20
        assert rect.width == 30
        assert rect.height == 40
        assert rect.left == 10
        assert rect.top == 20
        assert rect.right == 40
        assert rect.bottom == 60
        assert rect.center == Point(25, 40)
        assert not isinstance(rect, tuple)

    def test_rect_contains_point(self) -> None:
        rect = Rect(10, 10, 20, 20)
        # Inside
        assert Point(10, 10) in rect
        assert Point(20, 20) in rect
        assert Point(29, 29) in rect
        assert (15, 15) in rect

        # Outside (boundaries)
        assert Point(9, 10) not in rect
        assert Point(10, 9) not in rect
        assert Point(30, 15) not in rect  # right boundary is exclusive
        assert Point(15, 30) not in rect  # bottom boundary is exclusive
        assert (0, 0) not in rect

    def test_rect_iter(self) -> None:
        rect = Rect(0, 0, 3, 2)
        cells = list(rect)
        expected = [
            Point(0, 0), Point(1, 0), Point(2, 0),
            Point(0, 1), Point(1, 1), Point(2, 1),
        ]
        assert cells == expected
        assert len(cells) == 6

    def test_from_center(self) -> None:
        rect = Rect.from_center(center_x=30, center_y=15, width=20, height=10)
        assert rect.x == 20
        assert rect.y == 10
        assert rect.width == 20
        assert rect.height == 10
        assert rect.right == 40
        assert rect.bottom == 20
        assert rect.center == Point(30, 15)

    def test_from_corners(self) -> None:
        rect = Rect.from_corners(1, 1, 10, 10)
        assert rect.x == 1
        assert rect.y == 1
        assert rect.width == 10
        assert rect.height == 10
        assert rect.right == 11
        assert rect.bottom == 11

        # Inverted corners
        rect_inv = Rect.from_corners(10, 10, 1, 1)
        assert rect_inv == rect
