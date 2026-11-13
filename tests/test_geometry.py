"""
Unit tests for geometric primitives, Point, Size, and Rect in sanctuary/core/geometry.py.
"""
import pytest
from sanctuary.core.geometry import Point, Size, Rect, ray8, ray4
from sanctuary.core.primitives import Color


class TestColor:
    def test_from_hex(self) -> None:
        assert Color.from_hex("#0000ff") == Color(0, 0, 255)
        assert Color.from_hex("ff0000") == Color(255, 0, 0)
        assert Color.from_hex("#744231") == Color(116, 66, 49)

    def test_inverted(self) -> None:
        assert Color(0, 0, 0).inverted == Color(255, 255, 255)
        assert Color(255, 0, 128).inverted == Color(0, 255, 127)


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


class TestRays:
    def test_ray8_and_ray4_point_blank(self) -> None:
        pt = Point(5, 7)
        assert ray8(pt, pt) == [pt]
        assert ray4(pt, pt) == [pt]

    def test_ray8_diagonal_stepping(self) -> None:
        path = ray8(Point(0, 0), Point(4, 2))
        assert path == [
            Point(0, 0), Point(1, 0), Point(2, 1), Point(3, 1), Point(4, 2)
        ]

    def test_ray4_orthogonal_invariants(self) -> None:
        path = ray4(Point(0, 0), Point(4, 2))
        assert path == [
            Point(0, 0), Point(1, 0), Point(2, 0), Point(2, 1),
            Point(3, 1), Point(4, 1), Point(4, 2)
        ]
        # Invariant: Every step in ray4 must be strictly orthogonal (Manhattan distance == 1)
        for i in range(len(path) - 1):
            manhattan = abs(path[i + 1].x - path[i].x) + abs(path[i + 1].y - path[i].y)
            assert manhattan == 1

    def test_ray_all_directions(self) -> None:
        origin = Point(0, 0)
        targets = [
            Point(3, 0), Point(-3, 0), Point(0, 4), Point(0, -4),
            Point(2, 2), Point(-2, 2), Point(2, -2), Point(-2, -2),
            Point(5, 2), Point(-5, 2), Point(5, -2), Point(-5, -2),
        ]
        for target in targets:
            r8 = ray8(origin, target)
            r4 = ray4(origin, target)
            assert r8[0] == origin and r8[-1] == target
            assert r4[0] == origin and r4[-1] == target

            # Invariant: ray4 never steps diagonally
            for i in range(len(r4) - 1):
                assert abs(r4[i + 1].x - r4[i].x) + abs(r4[i + 1].y - r4[i].y) == 1

            # Invariant: ray8 never jumps more than 1 Chebyshev unit
            for i in range(len(r8) - 1):
                assert max(abs(r8[i + 1].x - r8[i].x), abs(r8[i + 1].y - r8[i].y)) == 1
