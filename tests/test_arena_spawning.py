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


from sanctuary.core.primitives import Color
from sanctuary.scenes.arena.faction import (
    ALL_FACTIONS,
    BLUE,
    BROWN,
    FACTIONS_BY_ID,
    FACTIONS_BY_NAME,
    Faction,
    GRAY,
    LIME,
    ORANGE,
    RED,
    TEAL,
    YELLOW,
)
from sanctuary.scenes.arena.gladiator import create_gladiator


def test_gladiator_faction_registry_and_textures() -> None:
    # 8 canonical AoE1 factions
    assert len(ALL_FACTIONS) == 8
    assert [f.id for f in ALL_FACTIONS] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert [f.name for f in ALL_FACTIONS] == [
        "Blue", "Red", "Yellow", "Brown", "Orange", "Lime", "Gray", "Teal"
    ]

    # Verify colors
    assert BLUE.color == Color(0, 0, 255)
    assert RED.color == Color(255, 0, 0)
    assert YELLOW.color == Color(255, 255, 0)
    assert BROWN.color == Color(116, 66, 49)
    assert ORANGE.color == Color(227, 115, 6)
    assert LIME.color == Color(0, 255, 0)
    assert GRAY.color == Color(192, 192, 192)
    assert TEAL.color == Color(0, 128, 128)

    # Verify lookup mappings
    assert FACTIONS_BY_ID[1] is BLUE
    assert FACTIONS_BY_ID[6] is LIME
    assert FACTIONS_BY_NAME["lime"] is LIME
    assert FACTIONS_BY_NAME["green"] is LIME

    # Verify create_gladiator with Faction object
    lime_g = create_gladiator(0, 0, 10, 100, 100, faction=LIME)
    assert lime_g.faction is LIME
    assert lime_g.alive_texture == LIME.alive_texture
    assert lime_g.dead_texture == LIME.dead_texture
    assert lime_g.alive_texture.glyph_1x1.cells[0][0].fg_color == Color(0, 255, 0)

    # Verify create_gladiator with string alias
    green_g = create_gladiator(0, 0, 10, 100, 100, faction="green")
    assert green_g.faction is LIME
    assert green_g.alive_texture == LIME.alive_texture

    yellow_g = create_gladiator(0, 0, 10, 100, 100, faction="yellow")
    assert yellow_g.faction is YELLOW
    assert yellow_g.alive_texture == YELLOW.alive_texture
    assert yellow_g.dead_texture == YELLOW.dead_texture
    assert yellow_g.alive_texture.glyph_1x1.cells[0][0].fg_color == Color(255, 255, 0)


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
