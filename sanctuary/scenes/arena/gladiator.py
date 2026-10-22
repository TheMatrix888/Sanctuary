"""
Gladiator actor model and evolutionary genome representation.
Encapsulates individual bytecode genomes, execution state, and team generation.
"""
from random import randint

from .config import GENOME_SIZE
from .entities import Entity
from .textures import (
    BLUE_GLADIATOR_TEXTURE,
    RED_GLADIATOR_TEXTURE,
    Texture,
)


class Gladiator:
    """
    Individual autonomous gladiator entity driven by a cyclic bytecode genome.
    """
    genome: list[int]
    genome_index: int
    entity: Entity

    def __init__(self, texture: Texture) -> None:
        self.genome = [randint(0, GENOME_SIZE) for _ in range(GENOME_SIZE)]
        self.genome_index = 0
        self.entity = Entity(
            x=0,
            y=0,
            texture=texture,
        )

    def turn(self) -> None:
        """Executes a single instruction step of the gladiator's genome."""
        gene = self.genome[self.genome_index]
        self.genome_index = (self.genome_index + 1) % len(self.genome)


def generate_team(gladiators: int, team: str) -> list[Gladiator]:
    """Factory creating a team of gladiators with the designated team texture."""
    texture = RED_GLADIATOR_TEXTURE if team == "red" else BLUE_GLADIATOR_TEXTURE
    return [Gladiator(texture) for _ in range(gladiators)]
