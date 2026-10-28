"""
Persistence and serialization layer for arena gladiator genomes and match benchmarks.
Saves and loads evolutionary dynasties to structured JSON bundles with versioning and metadata.
"""
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from sanctuary.core.geometry import Size

from .config import (
    BEST_PER_GENERATION,
    DEFAULT_ENTITIES_PER_TEAM,
    DEFAULT_MAP,
    EXCLUSION_HEIGHT,
    EXCLUSION_WIDTH,
    GENOME_SIZE,
    MAX_GENERATION_TURNS,
    MUTATION_RATE_PERCENT,
)
from .models import SimulationSave, WorldConfig

from .gladiator import Gladiator

SAVES_DIR: Path = Path("resources/simulation_saves")
SCHEMA_VERSION: int = 2










def get_saves_directory(directory: Path = SAVES_DIR) -> Path:
    """Ensures the target genome persistence directory exists and returns its resolved Path."""
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_simulation(
        teams: list[list[Gladiator]],
        generation: int,
        world_config: WorldConfig,
        directory: Path | None = None
) -> Path:
    """
    Serializes current active teams into a versioned JSON bundle.
    Generates a timestamped save file and updates latest.json for rapid access.
    """
    if len(teams) < 2:
        raise ValueError("Cannot save genome bundle: expected at least 2 teams (red, blue)")

    target_dir = get_saves_directory(directory) if directory else get_saves_directory()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    map_slug = "".join(char.lower() if char.isalnum() else "_" for char in world_config.map).strip("_")
    filename = f"{map_slug}_gen{generation}_{timestamp_str}.json"
    file_path = target_dir / filename

    config_dict = asdict(world_config)
    config_dict["initial_generation"] = generation

    payload: dict[str, Any] = {
        "version": SCHEMA_VERSION,
        "world_config": config_dict,
        "generation": generation,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "teams": {
            "red": [
                {"score": gladiator.score, "genome": gladiator.genome.copy()}
                for gladiator in teams[0]
            ],
            "blue": [
                {"score": gladiator.score, "genome": gladiator.genome.copy()}
                for gladiator in teams[1]
            ],
        },
    }

    content = json.dumps(payload, indent=4)
    file_path.write_text(content, encoding="utf-8")

    # Update latest.json
    latest_path = target_dir / "latest.json"
    latest_path.write_text(content, encoding="utf-8")

    return file_path


def load_simulation(file_path: Path) -> SimulationSave:
    """
    Parses a genome bundle from JSON, validating schema version and bytecode sizing.
    Returns ranked champion genomes sorted by score descending.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Genome save file not found: {path}")

    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    version = data.get("version", SCHEMA_VERSION)
    if version != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported genome save version: {version} (expected {SCHEMA_VERSION})"
        )

    generation = int(data.get("generation", 1))
    created_at = str(data.get("created_at", ""))

    config_data = data.get("world_config")
    if isinstance(config_data, dict):
        raw_exclusion = config_data.get("exclusion_size")
        if isinstance(raw_exclusion, (list, tuple)) and len(raw_exclusion) >= 2:
            exclusion_size = Size(int(raw_exclusion[0]), int(raw_exclusion[1]))
        elif isinstance(raw_exclusion, dict):
            exclusion_size = Size(
                int(raw_exclusion.get("width", EXCLUSION_WIDTH)),
                int(raw_exclusion.get("height", EXCLUSION_HEIGHT)),
            )
        elif "exclusion_width" in config_data and "exclusion_height" in config_data:
            exclusion_size = Size(
                int(config_data["exclusion_width"]),
                int(config_data["exclusion_height"]),
            )
        else:
            exclusion_size = Size(EXCLUSION_WIDTH, EXCLUSION_HEIGHT)

        world_config = WorldConfig(
            entities_per_team=int(config_data.get("entities_per_team", DEFAULT_ENTITIES_PER_TEAM)),
            map=str(config_data.get("map", DEFAULT_MAP)),
            max_turns=int(config_data.get("max_turns", MAX_GENERATION_TURNS)),
            best_per_generation=int(config_data.get("best_per_generation", BEST_PER_GENERATION)),
            mutation_rate_percent=float(config_data.get("mutation_rate_percent", MUTATION_RATE_PERCENT)),
            exclusion_size=exclusion_size,
            initial_generation=int(config_data.get("initial_generation", generation)),
        )
    else:
        world_config = WorldConfig(initial_generation=generation)

    teams_data = data.get("teams", {})
    red_raw = teams_data.get("red", [])
    blue_raw = teams_data.get("blue", [])

    # Sort each team by score descending
    red_sorted = sorted(red_raw, key=lambda item: item.get("score", 0), reverse=True)
    blue_sorted = sorted(blue_raw, key=lambda item: item.get("score", 0), reverse=True)

    red_genomes = [
        item["genome"]
        for item in red_sorted
        if isinstance(item.get("genome"), list) and len(item["genome"]) == GENOME_SIZE
    ]
    blue_genomes = [
        item["genome"]
        for item in blue_sorted
        if isinstance(item.get("genome"), list) and len(item["genome"]) == GENOME_SIZE
    ]

    return SimulationSave(
        version=version,
        world_config=world_config,
        generation=generation,
        created_at=created_at,
        red_genomes = red_genomes,
        blue_genomes = blue_genomes,
    )


def list_simulation_saves(directory: Path | None = None) -> list[str]:
    """
    Scans the genomes directory and returns all valid .json filenames sorted by recent modification.
    Places latest.json first if available.
    """
    target_dir = get_saves_directory(directory) if directory else get_saves_directory()
    json_files = [file for file in target_dir.glob("*.json") if file.is_file()]
    if not json_files:
        return []

    # Sort by modification time descending
    sorted_files = sorted(json_files, key=lambda p: p.stat().st_mtime, reverse=True)

    # Place latest.json at the top if present
    filenames: list[str] = []
    latest_name = "latest.json"
    has_latest = any(file.name == latest_name for file in sorted_files)

    if has_latest:
        filenames.append(latest_name)

    for file_path in sorted_files:
        if file_path.name != latest_name:
            filenames.append(file_path.name)

    return filenames
