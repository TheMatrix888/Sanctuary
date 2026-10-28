"""
Unit tests for numerical formatting and metric compactification.
"""
import pytest
from sanctuary.core.formatting import format_compact


@pytest.mark.parametrize(
    "input_val, expected",
    [
        (0, "0"),
        (5, "5"),
        (-42, "-42"),
        (999, "999"),
        (1000, "1K"),
        (1050, "1.1K"),
        (1200, "1.2K"),
        (9900, "9.9K"),
        (10000, "10K"),
        (134942, "134.9K"),
        (999950, "1M"),
        (1000000, "1M"),
        (1200000, "1.2M"),
        (45600000, "45.6M"),
        (1000000000, "1B"),
        (2500000000, "2.5B"),
        (1000000000000, "1T"),
        (1000000000000000, "1Q"),
        (2500000000000000, "2.5Q"),
        (-1500, "-1.5K"),
        (-2500000, "-2.5M"),
    ],
)
def test_format_compact_defaults(input_val: float | int, expected: str) -> None:
    assert format_compact(input_val) == expected


def test_format_compact_precision() -> None:
    assert format_compact(123456, precision=2) == "123.46K"
    assert format_compact(123456, precision=0) == "123K"
    assert format_compact(1200000, precision=2) == "1.2M"
    assert format_compact(1250000, precision=2) == "1.25M"
