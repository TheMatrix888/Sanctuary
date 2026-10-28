"""
End-to-end integration test for arena genome persistence, UI dropdown loading, and worker team seeding.
"""
from multiprocessing import Event, Queue
from sanctuary.core.geometry import Size
from sanctuary.scenes.arena.config import GENOME_SIZE
from sanctuary.scenes.arena.gladiator import create_gladiator
from sanctuary.scenes.arena.persistence import save_simulation
from sanctuary.scenes.arena.simulation import ArenaSimulation
from sanctuary.scenes.arena.models import (
    GenerationRecord,
    Mode,
    PlaybackSettings,
    Snapshot,
)
from sanctuary.scenes.arena.worker import SimulationWorker


def test_arena_simulation_save_and_load_flow(tmp_path, monkeypatch) -> None:
    # Point persistence directory to tmp_path
    monkeypatch.setattr("sanctuary.scenes.arena.persistence.SAVES_DIR", tmp_path)

    sim = ArenaSimulation()
    assert sim.save_button.label == "Save latest snapshot genome [None]"

    # Attempting to save without snapshot shows warning
    sim._on_save_genome()
    assert "No simulation snapshot" in sim.status_message

    # Create mock snapshot
    red_g1 = create_gladiator(0, 0, 10, 100, 100, "red", genome=[77] * GENOME_SIZE)
    red_g1.score = 500
    blue_g1 = create_gladiator(0, 0, 10, 100, 100, "blue", genome=[88] * GENOME_SIZE)
    blue_g1.score = 450

    mock_snapshot = Snapshot(
        teams=[[red_g1], [blue_g1]],
        tilemap=sim.map_preview,
        turn=10,
        generation=25,
        record=GenerationRecord(generation=25, turns=10, survivors=2),
    )
    sim.last_snapshot = mock_snapshot
    sim._update_active_items()
    assert sim.save_button.label == "Save latest snapshot genome (Gen 25)"

    # Save genome
    sim._on_save_genome()
    assert "Saved:" in sim.status_message
    assert len(sim.load_dropdown.options) >= 2  # timestamped + latest.json

    # Load genome via dropdown callback
    sim._on_genome_loaded(sim.load_dropdown.options[0])
    assert "Loaded" in sim.status_message
    assert sim.loaded_genomes is not None
    assert sim.loaded_genomes["red"][0] == [77] * GENOME_SIZE
    assert sim.loaded_genomes["blue"][0] == [88] * GENOME_SIZE

    # Gather world config and verify initial_genomes and initial_generation populated
    world_config = sim.gather_world_config()
    assert world_config.initial_genomes == sim.loaded_genomes
    assert world_config.initial_generation == 25

    # Instantiate SimulationWorker and verify seeded gladiator simulation_saves and generation continuation
    worker = SimulationWorker(
        world_config=world_config,
        playback_settings=PlaybackSettings(snapshots_per_second=10.0, mode=Mode.SIMULATION),
        playback_settings_queue=Queue(),
        snapshot_queue=Queue(),
        stop_event=Event(),
    )
    assert worker.generation == 25
    assert worker.record.generation == 25

    # Every gladiator should inherit the seeded champion genome
    for gladiator in worker.red_team:
        assert gladiator.genome == [77] * GENOME_SIZE
    for gladiator in worker.blue_team:
        assert gladiator.genome == [88] * GENOME_SIZE


def test_stop_simulation_preserves_last_snapshot() -> None:
    sim = ArenaSimulation()
    sim.is_running = True

    # Put snapshot into queue
    red_g1 = create_gladiator(0, 0, 10, 100, 100, "red", genome=[99] * GENOME_SIZE)
    blue_g1 = create_gladiator(0, 0, 10, 100, 100, "blue", genome=[99] * GENOME_SIZE)
    snap = Snapshot(
        teams=[[red_g1], [blue_g1]],
        tilemap=sim.map_preview,
        turn=5,
        generation=42,
        record=GenerationRecord(generation=42, turns=5, survivors=2),
    )
    sim.snapshot_queue.put(snap)

    # Stop simulation
    sim._toggle_simulation()
    assert sim.is_running is False
    assert sim.last_snapshot is not None
    assert sim.last_snapshot.generation == 42
    assert sim.save_button.label == "Save latest snapshot genome (Gen 42)"
