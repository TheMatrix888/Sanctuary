"""
Unit tests for the Dropdown form widget and modal focus capture in FormState.
"""
from sanctuary.core.geometry import Size
from sanctuary.core.input_handler import Key
from sanctuary.core.screen import Screen
from sanctuary.core.terminal import VirtualTerminal
from sanctuary.ui.form import FormState
from sanctuary.ui.widgets import Button, Dropdown, FormItem


class MockInput:
    def __init__(self, pressed: list[Key] | None = None, repeated: list[Key] | None = None):
        self._pressed = pressed or []
        self._repeated = repeated or []

    def just_pressed(self, key: Key) -> bool:
        return key in self._pressed

    def is_pressed(self, key: Key) -> bool:
        return key in self._pressed or key in self._repeated

    def is_repeated(self, key: Key) -> bool:
        return key in self._repeated


def test_dropdown_basic_lifecycle() -> None:
    selected = []
    dropdown = Dropdown(
        label="Saved Genomes",
        options=["alpha.json", "beta.json", "gamma.json"],
        on_select=lambda val: selected.append(val),
    )
    assert dropdown.value == "alpha.json"
    assert dropdown.render_value() == "[alpha.json ▼]"
    assert not dropdown.is_capturing_input

    # Adjusting when closed cycles option
    dropdown.on_adjust(1)
    assert dropdown.value == "beta.json"

    # Activation opens dropdown and captures input
    dropdown.on_activate()
    assert dropdown.is_open is True
    assert dropdown.is_capturing_input is True
    assert dropdown.render_value() == "[beta.json ▲]"

    # Sub-navigation inside dropdown via handle_input
    mock_down = MockInput(repeated=[Key.DOWN])
    dropdown.handle_input(mock_down)
    assert dropdown.value == "gamma.json"

    mock_enter = MockInput(pressed=[Key.ENTER])
    dropdown.handle_input(mock_enter)
    assert dropdown.is_open is False
    assert dropdown.is_capturing_input is False
    assert selected == ["gamma.json"]


def test_dropdown_modal_focus_in_form_state() -> None:
    dropdown = Dropdown(
        label="Genomes",
        options=["file1.json", "file2.json", "file3.json"],
    )
    button = Button("Start")
    form = FormState(title="Test Form", items=[dropdown, button])

    assert form.index == 0

    # Open dropdown with Enter
    form.handle_input(MockInput(pressed=[Key.ENTER]))
    assert dropdown.is_open is True

    # Pressing Down should NOT advance form.index to button, but advance dropdown option!
    form.handle_input(MockInput(repeated=[Key.DOWN]))
    assert form.index == 0
    assert dropdown.value == "file2.json"

    # Pressing Esc should close dropdown without advancing form
    form.handle_input(MockInput(pressed=[Key.ESC]))
    assert dropdown.is_open is False
    assert form.index == 0

    # Now pressing Down advances form.index to button
    form.handle_input(MockInput(repeated=[Key.DOWN]))
    assert form.index == 1


def test_dropdown_draw_expanded() -> None:
    terminal = VirtualTerminal(columns=80, rows=25)
    screen = Screen(terminal)
    dropdown = Dropdown(
        label="Genomes",
        options=["colosseum.json", "bastions.json"],
        is_open=True,
    )
    form = FormState(title="Test", items=[dropdown])
    form.draw(screen)

    # Verify dropdown options rendered on screen back_buffer
    rendered_chars = "".join(cell.char for row in screen.back_buffer.cells for cell in row)
    assert "colosseum.json" in rendered_chars
    assert "bastions.json" in rendered_chars


def test_base_form_item_defaults() -> None:
    class DummyItem(FormItem):
        def render_value(self) -> str:
            return ""

        def on_adjust(self, delta: int, multiplier: float = 1.0) -> None:
            pass

        def on_activate(self):
            return None

        def on_reset(self) -> None:
            pass

        def get_help_hint(self) -> str:
            return ""

    dummy = DummyItem()
    dummy.label = "Dummy"
    assert dummy.is_capturing_input is False
    assert dummy.handle_input(MockInput()) is None
    terminal = VirtualTerminal(columns=80, rows=25)
    screen = Screen(terminal)
    assert dummy.draw_expanded(screen, 0, 5, 20) == 5
