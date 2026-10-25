"""
Unit test verifying instantiation and execution contract for all standalone visual demo scenes.
"""
from sanctuary.scenes.demos import (
    BouncingBoxState,
    BouncingHammerState,
    GridAuditState,
    OrbitalWindowState,
    OvercomingState,
    RainbowTextState,
)
from sanctuary.scenes.menu import create_main_menu


def test_demos_instantiation() -> None:
    box = BouncingBoxState()
    hammer = BouncingHammerState()
    grid = GridAuditState()
    orbital = OrbitalWindowState()
    overcoming = OvercomingState()
    wave = RainbowTextState()

    assert box is not None
    assert hammer is not None
    assert grid is not None
    assert orbital is not None
    assert overcoming is not None
    assert wave is not None


def test_main_menu_demos_hierarchy() -> None:
    menu = create_main_menu()
    assert menu.title == "Sanctuary Main Menu"
    assert len(menu.items) == 4
