"""
Unit tests for genome persistence, serialization, and version validation.
"""
import pytest
from sanctuary.core.geometry import Size
from sanctuary.scenes.arena.config import GENOME_SIZE
from sanctuary.scenes.arena.gladiator import create_gladiator
from sanctuary.scenes.arena.models import WorldConfig
from sanctuary.scenes.arena.persistence import (
    SCHEMA_VERSION,
    list_simulation_saves,
    load_simulation,
    save_simulation,
)


def test_save_and_load_genome_bundle(tmp_path) -> None:
    red_g1 = create_gladiator(0, 0, 10, 100, 100, "red", genome=[1] * GENOME_SIZE)
    red_g1.score = 50
    red_g2 = create_gladiator(0, 0, 10, 100, 100, "red", genome=[2] * GENOME_SIZE)
    red_g2.score = 200  # Champion

    blue_g1 = create_gladiator(0, 0, 10, 100, 100, "blue", genome=[3] * GENOME_SIZE)
    blue_g1.score = 120

    teams = [[red_g1, red_g2], [blue_g1]]

    saved_file = save_simulation(
        teams=teams,
        generation=15,
        world_config=WorldConfig(map="Colosseum Arena"),
        directory=tmp_path,
    )

    assert saved_file.is_file()
    assert (tmp_path / "latest.json").is_file()

    # Load from saved file
    bundle = load_simulation(saved_file)
    assert bundle.version == SCHEMA_VERSION
    assert bundle.generation == 15
    assert bundle.world_config.map == "Colosseum Arena"

    # Red champion (score 200) must be first
    assert len(bundle.red_genomes) == 2
    assert bundle.red_genomes[0] == [2] * GENOME_SIZE
    assert bundle.red_genomes[1] == [1] * GENOME_SIZE

    # Blue champion
    assert len(bundle.blue_genomes) == 1
    assert bundle.blue_genomes[0] == [3] * GENOME_SIZE

    # Test list_saved_genomes
    files = list_simulation_saves(tmp_path)
    assert len(files) == 2
    assert files[0] == "latest.json"
    assert files[1] == saved_file.name


def test_version_validation_failure(tmp_path) -> None:
    bad_file = tmp_path / "corrupt.json"
    bad_file.write_text('{"version": 999, "teams": {}}', encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported genome save version: 999"):
        load_simulation(bad_file)


def test_load_exclusion_formats(tmp_path) -> None:
    # 1. List/tuple format (standard JSON serialization of NamedTuple)
    f1 = tmp_path / "save_list.json"
    f1.write_text('{"version": 2, "world_config": {"exclusion_size": [25, 15]}}', encoding="utf-8")
    s1 = load_simulation(f1)
    assert s1.world_config.exclusion_size == Size(25, 15)

    # 2. Dict format
    f2 = tmp_path / "save_dict.json"
    f2.write_text('{"version": 2, "world_config": {"exclusion_size": {"width": 25, "height": 15}}}', encoding="utf-8")
    s2 = load_simulation(f2)
    assert s2.world_config.exclusion_size == Size(25, 15)

    # 3. Flat legacy keys
    f3 = tmp_path / "save_flat.json"
    f3.write_text('{"version": 2, "world_config": {"exclusion_width": 25, "exclusion_height": 15}}', encoding="utf-8")
    s3 = load_simulation(f3)
    assert s3.world_config.exclusion_size == Size(25, 15)
