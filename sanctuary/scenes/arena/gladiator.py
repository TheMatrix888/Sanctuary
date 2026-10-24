"""
Gladiator actor model and evolutionary genome representation.
Encapsulates individual bytecode genomes, execution state, and gladiator creation.
"""
from dataclasses import dataclass
from random import randint

from .config import ARENA_HEIGHT, ARENA_WIDTH, GENOME_SIZE
from .entities import Entity
from .textures import (
    BLUE_GLADIATOR_TEXTURE,
    DEAD_BLUE_GLADIATOR_TEXTURE,
    DEAD_RED_GLADIATOR_TEXTURE,
    RED_GLADIATOR_TEXTURE,
    Texture,
)


@dataclass(slots=True)
class Gladiator(Entity):
    """
    Autonomous evolutionary combatant driven by ring-buffer bytecode VM.
    Fields strictly follow: Entity spatial/physical -> Visual assets -> Identity -> Runtime state.
    """
    alive_texture: Texture
    dead_texture: Texture
    faction: str
    genome: list[int]
    pc: int
    score: int
    spawn_x: int
    spawn_y: int
    min_distance: int

    @property
    def current_gene(self) -> int:
        return self.genome[self.pc]

    def set_position(self, x: int, y: int) -> None:
        """Sets gladiator coordinates and initializes spawn benchmark position."""
        self.x = x
        self.y = y
        self.spawn_x = x
        self.spawn_y = y
        center_x = ARENA_WIDTH // 2
        center_y = ARENA_HEIGHT // 2
        self.min_distance = abs(x - center_x) + abs(y - center_y)

    def record_distance(self, center_x: int, center_y: int) -> None:
        """Updates the high-water mark minimum distance achieved toward the arena center."""
        current_distance = abs(self.x - center_x) + abs(self.y - center_y)
        if current_distance < self.min_distance:
            self.min_distance = current_distance

    def resurrect(self) -> None:
        """Restores full health and living texture for a new generation round."""
        self.hp = self.max_hp
        self.texture = self.alive_texture
        self.pc = 0


def create_gladiator(
    x: int,
    y: int,
    view_distance: int,
    hp: int,
    max_hp: int,
    faction: str,
    genome: list[int] | None = None,
) -> Gladiator:
    """
    Factory creating an autonomous gladiator entity with genome and faction textures.
    Instantiates fields in the exact schema declaration order.
    """
    texture = RED_GLADIATOR_TEXTURE if faction == "red" else BLUE_GLADIATOR_TEXTURE
    dead_texture = DEAD_RED_GLADIATOR_TEXTURE if faction == "red" else DEAD_BLUE_GLADIATOR_TEXTURE
    actual_genome = genome if genome is not None else [randint(0, GENOME_SIZE - 1) for _ in range(GENOME_SIZE)]
    center_x = ARENA_WIDTH // 2
    center_y = ARENA_HEIGHT // 2
    initial_distance = abs(x - center_x) + abs(y - center_y)

    return Gladiator(
        x=x,
        y=y,
        view_distance=view_distance,
        hp=hp,
        max_hp=max_hp,
        texture=texture,
        alive_texture=texture,
        dead_texture=dead_texture,
        faction=faction,
        genome=actual_genome,
        pc=0,
        score=0,
        spawn_x=x,
        spawn_y=y,
        min_distance=initial_distance,
    )
