"""
Unit test for ArenaSimulation form state, exclusion zone knobs, blinking timer, and Toggle widget.
"""
from sanctuary.core.config import DisplayConfig
from sanctuary.core.geometry import Rect, Size
from sanctuary.core.primitives import Color
from sanctuary.core.screen import Screen
from sanctuary.core.terminal import VirtualTerminal
from sanctuary.scenes.arena.config import ARENA_HEIGHT, ARENA_WIDTH
from sanctuary.scenes.arena.generators import generate_tectonic_chasm
from sanctuary.scenes.arena.models import BlinkIndicator, GpsTracker, WorldConfig
from sanctuary.scenes.arena.simulation import ArenaSimulation
from sanctuary.scenes.arena.tiles import BLOOD_FLOOR
from sanctuary.ui.widgets import Toggle


def test_arena_simulation_widgets_and_config() -> None:
    sim = ArenaSimulation()
    assert sim.entities_knob.value == 10
    assert sim.max_turns_knob.value == 200
    assert sim.champions_knob.value == 4
    assert sim.mutation_rate_knob.value == 2.0
    assert sim.exclusion_width_knob.value == 20
    assert sim.exclusion_height_knob.value == 10
    assert sim.exclusion_blink_toggle.value is True

    # Adjust values
    sim.entities_knob.on_adjust(1, multiplier=1.0)
    sim.max_turns_knob.on_adjust(1, multiplier=1.0)
    sim.champions_knob.on_adjust(1, multiplier=1.0)
    sim.mutation_rate_knob.on_adjust(1, multiplier=1.0)
    sim.exclusion_width_knob.on_adjust(2, multiplier=1.0)
    sim.exclusion_height_knob.on_adjust(-1, multiplier=1.0)
    sim.exclusion_blink_toggle.on_adjust(1, multiplier=1.0)

    config = sim.gather_world_config()
    assert isinstance(config, WorldConfig)
    assert config.entities_per_team == 11
    assert config.max_turns == 210
    assert config.best_per_generation == 5
    assert config.mutation_rate_percent == 2.5
    assert config.exclusion_size.width == 22
    assert config.exclusion_size.height == 9
    assert sim.exclusion_blink_toggle.value is False


def test_exclusion_zone_blinking_timer() -> None:
    sim = ArenaSimulation()
    assert sim._exclusion_visible is True

    # Tick 0.5s -> should toggle to False
    sim.update(0.5, Size(width=100, height=40))
    assert sim._exclusion_visible is False

    # Tick another 0.5s -> should toggle back to True
    sim.update(0.5, Size(width=100, height=40))
    assert sim._exclusion_visible is True


def test_toggle_widget_activation_and_reset() -> None:
    toggle = Toggle("Blink exclusion", is_enabled=True)
    assert toggle.value is True
    assert toggle.render_value() == "[On]"

    toggle.on_activate()
    assert toggle.value is False
    assert toggle.render_value() == "[Off]"

    toggle.on_reset()
    assert toggle.value is True
    assert toggle.render_value() == "[On]"


def test_champions_knob_dynamic_limiter() -> None:
    sim = ArenaSimulation()
    assert sim.entities_knob.value == 10
    assert sim.champions_knob.value == 4
    assert sim.champions_knob.max_value == 10

    # Reduce entities to 2
    sim.entities_knob.value = 2
    sim.update(0.1, Size(width=100, height=40))

    # Champions knob clamped to 2 and max_value clamped to 2
    assert sim.champions_knob.max_value == 2
    assert sim.champions_knob.value == 2

    # Attempting to adjust champions up should be capped at 2
    sim.champions_knob.on_adjust(5, multiplier=1.0)
    assert sim.champions_knob.value == 2

    # Expanding entities to 25 should expand champions max_value to 25
    sim.entities_knob.value = 25
    sim.update(0.1, Size(width=100, height=40))
    assert sim.champions_knob.max_value == 25
    sim.champions_knob.on_adjust(10, multiplier=1.0)
    assert sim.champions_knob.value == 12


def test_tectonic_chasm_3x3_center() -> None:
    tilemap = generate_tectonic_chasm(ARENA_WIDTH, ARENA_HEIGHT)
    center_x = ARENA_WIDTH // 2
    center_y = ARENA_HEIGHT // 2

    blood_cells_count = 0
    for delta_y in (-1, 0, 1):
        for delta_x in (-1, 0, 1):
            if tilemap.get_tile(center_x + delta_x, center_y + delta_y) == BLOOD_FLOOR:
                blood_cells_count += 1

    assert blood_cells_count == 9, f"Expected 9 blood floor cells in 3x3 center, found {blood_cells_count}"


def test_gps_tracker() -> None:
    tracker = GpsTracker(interval=0.5)
    assert tracker.rate == 0.0

    # Reset with custom initial generation
    tracker.reset(initial_generation=50)
    assert tracker.rate == 0.0
    assert tracker._last_generation == 50

    # Advance time artificially
    tracker._last_time -= 0.6
    tracker.update(current_generation=60)
    assert tracker.rate > 0.0
    assert tracker._last_generation == 60


def test_blink_indicator() -> None:
    blinker = BlinkIndicator(interval=0.5)
    assert blinker.is_visible is True

    # Advance 0.3s -> no change
    toggled = blinker.tick(0.3)
    assert toggled is False
    assert blinker.is_visible is True

    # Advance 0.2s -> expired, toggled to False
    toggled = blinker.tick(0.2)
    assert toggled is True
    assert blinker.is_visible is False

    # Reset -> restores visibility
    blinker.reset()
    assert blinker.is_visible is True


def test_screen_fill_rect() -> None:
    terminal = VirtualTerminal()
    display = DisplayConfig(columns=80, rows=25)
    screen = Screen(terminal, display)

    rect = Rect(10, 5, 4, 3)
    fill_color = Color(255, 100, 50)
    screen.fill_rect(rect, char="#", fg_color=fill_color)

    for point in rect:
        cell = screen.back_buffer.cells[point.y][point.x]
        assert cell.char == "#"
        assert cell.fg_color == fill_color

    # Cell outside rect is untouched
    outside = screen.back_buffer.cells[5][9]
    assert outside.char == " "

    # Fill rect clipping against screen boundary without exception
    boundary_rect = Rect(75, 20, 10, 10)
    screen.fill_rect(boundary_rect, char="@")
    assert screen.back_buffer.cells[24][79].char == "@"
