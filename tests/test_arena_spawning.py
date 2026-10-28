"""
Unit test for gladiator spawning in arena worker with the center exclusion zone.
"""
from multiprocessing import Queue
import multiprocessing

from sanctuary.core.geometry import Point, Rect, Size
from sanctuary.scenes.arena.config import ARENA_WIDTH, ARENA_HEIGHT, GENOME_SIZE
from sanctuary.scenes.arena.models import (
    Mode,
    PlaybackSettings,
    WorldConfig,
)
from sanctuary.scenes.arena.worker import SimulationWorker


def test_gladiator_spawning_avoids_center_exclusion() -> None:
    playback_queue = Queue()
    snapshot_queue = Queue()
    stop_event = multiprocessing.Event()

    config = WorldConfig(
        entities_per_team=10,
        map="Colosseum Arena",
        exclusion_size=Size(ARENA_WIDTH // 3, ARENA_HEIGHT // 3),
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
        width=config.exclusion_size.width,
        height=config.exclusion_size.height,
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


def test_uniform_per_gene_mutation() -> None:
    playback_queue = Queue()
    snapshot_queue = Queue()
    stop_event = multiprocessing.Event()

    # Zero mutation rate test -> perfect preservation
    zero_config = WorldConfig(
        entities_per_team=10,
        map="Colosseum Arena",
        best_per_generation=1,
        mutation_rate_percent=0.0,
    )
    settings = PlaybackSettings(snapshots_per_second=10.0, mode=Mode.SIMULATION)
    worker_zero = SimulationWorker(
        world_config=zero_config,
        playback_settings=settings,
        playback_settings_queue=playback_queue,
        snapshot_queue=snapshot_queue,
        stop_event=stop_event,
    )
    # Give champion a known genome
    worker_zero.red_team[0].score = 9999
    expected_genome = [42] * GENOME_SIZE
    worker_zero.red_team[0].genome = expected_genome.copy()

    worker_zero.new_generation()

    # All descendants of champion must have identical genome with zero mutations
    for gladiator in worker_zero.red_team:
        assert gladiator.genome == expected_genome

    # 100% mutation rate test -> champion preserved, all descendant genes modified with high probability
    full_config = WorldConfig(
        entities_per_team=10,
        map="Colosseum Arena",
        best_per_generation=1,
        mutation_rate_percent=100.0,
    )
    worker_full = SimulationWorker(
        world_config=full_config,
        playback_settings=settings,
        playback_settings_queue=playback_queue,
        snapshot_queue=snapshot_queue,
        stop_event=stop_event,
    )
    worker_full.red_team[0].score = 9999
    worker_full.red_team[0].genome = expected_genome.copy()

    worker_full.new_generation()

    # Champion (index 0) remains 100% preserved
    assert worker_full.red_team[0].genome == expected_genome
    # Descendants must have suffered mass mutations
    for gladiator in worker_full.red_team[1:]:
        assert gladiator.genome != expected_genome
