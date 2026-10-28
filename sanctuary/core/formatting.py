"""
Text and numerical formatting utilities for compact metrics and telemetry displays.
Translates large numbers (thousands, millions, billions) into clean, human-readable strings with metric suffixes.
"""
SUFFIXES: tuple[tuple[float, str], ...] = (
    (1e3, "K"),
    (1e6, "M"),
    (1e9, "B"),
    (1e12, "T"),
    (1e15, "Q"),
)


def format_compact(value: float | int, precision: int = 1) -> str:
    """Formats a large numeric value into a concise human-readable representation with metric suffix."""
    if abs(value) < 1000:
        if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
            return str(int(value))
        return f"{value:.{precision}f}".rstrip("0").rstrip(".")

    sign = "-" if value < 0 else ""
    abs_val = abs(value)

    for threshold, suffix in reversed(SUFFIXES):
        scaled = abs_val / threshold
        if round(scaled, precision) >= 1.0:
            formatted = f"{scaled:.{precision}f}".rstrip("0").rstrip(".")
            return f"{sign}{formatted}{suffix}"

    return str(value)
