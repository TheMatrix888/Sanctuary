"""
Unit test for gladiator spawning in arena worker with the center exclusion zone.
"""
from multiprocessing import Queue
import multiprocessing

from sanctuary.core.geometry import Point, Rect
from sanctuary.scenes.arena.config import ARENA_WIDTH, ARENA_HEIGHT
from sanctuary.scenes.arena.worker import (
    SimulationWorker,
    WorldConfig,
    PlaybackSettings,
    Mode,
)


def test_gladiator_spawning_avoids_center_exclusion() -> None:
    playback_queue = Queue()
    snapshot_queue = Queue()
    stop_event = multiprocessing.Event()

    config = WorldConfig(
        entities_per_team=10,
        map="Colosseum Arena",
        exclusion_width=ARENA_WIDTH // 3,
        exclusion_height=ARENA_HEIGHT // 3,
    )
    settings = PlaybackSettings(snapshots_per_second=10.0, mode=Mode.SIMULATION)

    worker = SimulationWorker(
        world_config=config,
        playback_settings=settings,
        playback_settings_queue=playback_queue,
        snapshot_queue=snapshot_queue,
        stop_event=stop_event,
    )

    exclusion_rect = Rect.from_center(
        center_x=ARENA_WIDTH // 2,
        center_y=ARENA_HEIGHT // 2,
        width=config.exclusion_width,
        height=config.exclusion_height,
    )

    # Check 50 consecutive team positionings across generations
    for _ in range(50):
        worker.position_teams()
        for gladiator in worker.red_team + worker.blue_team:
            position = Point(gladiator.x, gladiator.y)
            # Guarantee gladiator is NEVER inside the center exclusion box
            assert position not in exclusion_rect, f"Gladiator spawned inside exclusion zone at {position}"
            # Guarantee gladiator is on walkable floor
            assert worker.tilemap.is_walkable(position.x, position.y), f"Gladiator spawned on non-walkable tile at {position}"
