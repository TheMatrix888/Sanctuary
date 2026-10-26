"""
Persistence and serialization layer for arena gladiator genomes and match benchmarks.
Saves and loads evolutionary dynasties to structured JSON bundles with versioning and metadata.
"""
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from .config import GENOME_SIZE
from .gladiator import Gladiator

DEFAULT_GENOMES_DIR: Path = Path("resources/genomes")
SCHEMA_VERSION: int = 1


def get_genomes_directory(base_dir: Path | str | None = None) -> Path:
    """Ensures the target genome persistence directory exists and returns its resolved Path."""
    target_dir = Path(base_dir) if base_dir is not None else DEFAULT_GENOMES_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def save_genome_bundle(
    teams: list[list[Gladiator]],
    generation: int,
    map_name: str,
    directory: Path | str | None = None,
) -> Path:
    """
    Serializes current active teams into a versioned JSON bundle.
    Generates a timestamped save file and updates latest.json for rapid access.
    """
    if len(teams) < 2:
        raise ValueError("Cannot save genome bundle: expected at least 2 teams (red, blue)")

    target_dir = get_genomes_directory(directory)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    map_slug = "".join(char.lower() if char.isalnum() else "_" for char in map_name).strip("_")
    filename = f"{map_slug}_gen{generation}_{timestamp_str}.json"
    file_path = target_dir / filename

    payload: dict[str, Any] = {
        "version": SCHEMA_VERSION,
        "map": map_name,
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

    content = json.dumps(payload, indent=2)
    file_path.write_text(content, encoding="utf-8")

    # Update latest.json
    latest_path = target_dir / "latest.json"
    latest_path.write_text(content, encoding="utf-8")

    return file_path


def load_genome_bundle(file_path: Path | str) -> dict[str, Any]:
    """
    Parses a genome bundle from JSON, validating schema version and bytecode sizing.
    Returns ranked champion genomes sorted by score descending.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Genome save file not found: {path}")

    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    version = data.get("version")
    if version != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported genome save version: {version} (expected {SCHEMA_VERSION})"
        )

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

    return {
        "version": version,
        "map": data.get("map", ""),
        "generation": data.get("generation", 1),
        "created_at": data.get("created_at", ""),
        "red_genomes": red_genomes,
        "blue_genomes": blue_genomes,
    }


def list_saved_genomes(directory: Path | str | None = None) -> list[str]:
    """
    Scans the genomes directory and returns all valid .json filenames sorted by recent modification.
    Places latest.json first if available.
    """
    target_dir = get_genomes_directory(directory)
    json_files = [f for f in target_dir.glob("*.json") if f.is_file()]
    if not json_files:
        return []

    # Sort by modification time descending
    sorted_files = sorted(json_files, key=lambda p: p.stat().st_mtime, reverse=True)

    # Place latest.json at the top if present
    filenames: list[str] = []
    latest_name = "latest.json"
    has_latest = any(f.name == latest_name for f in sorted_files)

    if has_latest:
        filenames.append(latest_name)

    for file_path in sorted_files:
        if file_path.name != latest_name:
            filenames.append(file_path.name)

    return filenames
