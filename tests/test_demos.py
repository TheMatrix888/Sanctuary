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


def test_transient_vs_retained_states() -> None:
    menu = create_main_menu()
    # Arena is transient (callable action returning fresh instance)
    arena_btn = menu.items[0]
    assert callable(arena_btn.action)
    cmd1 = arena_btn.action()
    cmd2 = arena_btn.action()
    assert cmd1.state is not cmd2.state

    # Arena simulation is retained (direct Push command holding singleton instance)
    sim_btn = menu.items[1]
    assert not callable(sim_btn.action)
    assert sim_btn.action.state is not None
