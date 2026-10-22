"""
Multi-resolution Texture assets for the tactical arena.
Decouples visual Surface representations entirely from physical tile material properties.
"""
from dataclasses import dataclass

from sanctuary.core.primitives import Cell, Color, Surface


@dataclass(slots=True, frozen=True)
class Texture:
    """
    Multi-resolution visual asset containing pre-rendered Surface representations
    for 1x1, 2x1 (aspect-ratio corrected), 2x2 (humanoid tall block), and 4x2 footprints.
    """
    glyph_1x1: Surface
    glyph_2x1: Surface
    glyph_2x2: Surface
    glyph_4x2: Surface

    def get_surface(self, scale: tuple[int, int] = (1, 1)) -> Surface:
        """Retrieves the corresponding Surface for the target footprint scale."""
        if scale == (4, 2):
            return self.glyph_4x2
        if scale == (2, 2):
            return self.glyph_2x2
        if scale == (2, 1):
            return self.glyph_2x1
        return self.glyph_1x1


# =============================================================================
# ENVIRONMENT & TERRAIN TEXTURES
# =============================================================================

WALL_TEXTURE = Texture(
    glyph_1x1=Surface("#", fg_color=Color(192, 192, 192)),
    glyph_2x1=Surface("##", fg_color=Color(192, 192, 192)),
    glyph_2x2=Surface("┌┐\n└┘", fg_color=Color(192, 192, 192)),
    glyph_4x2=Surface("╔══╗\n╚══╝", fg_color=Color(192, 192, 192)),
)

FLOOR_TEXTURE = Texture(
    glyph_1x1=Surface(".", fg_color=Color(80, 80, 90)),
    glyph_2x1=Surface(". ", fg_color=Color(80, 80, 90)),
    glyph_2x2=Surface(". \n  ", fg_color=Color(80, 80, 90)),
    glyph_4x2=Surface(".   \n    ", fg_color=Color(80, 80, 90)),
)

BLOOD_FLOOR_TEXTURE = Texture(
    glyph_1x1=Surface(".", fg_color=Color(160, 20, 20)),
    glyph_2x1=Surface(". ", fg_color=Color(160, 20, 20)),
    glyph_2x2=Surface(". \n  ", fg_color=Color(160, 20, 20)),
    glyph_4x2=Surface(".   \n    ", fg_color=Color(160, 20, 20)),
)

CHASM_TEXTURE = Texture(
    glyph_1x1=Surface("≈", fg_color=Color(60, 120, 220)),
    glyph_2x1=Surface("≈≈", fg_color=Color(60, 120, 220)),
    glyph_2x2=Surface("≈≈\n≈≈", fg_color=Color(60, 120, 220)),
    glyph_4x2=Surface("≈≈≈≈\n≈≈≈≈", fg_color=Color(60, 120, 220)),
)

# =============================================================================
# ACTOR & GLADIATOR TEXTURES
# =============================================================================

PLAYER_TEXTURE = Texture(
    glyph_1x1=Surface("☺", fg_color=Color(128, 0, 255)),
    glyph_2x1=Surface("☺ ", fg_color=Color(128, 0, 255)),
    glyph_2x2=Surface("☺ \n/\\", fg_color=Color(128, 0, 255)),
    glyph_4x2=Surface("o_o]\n/||\\", fg_color=Color(128, 0, 255)),
)

RED_GLADIATOR_TEXTURE = Texture(
    glyph_1x1=Surface("☺", fg_color=Color(255, 0, 0)),
    glyph_2x1=Surface("☺ ", fg_color=Color(255, 0, 0)),
    glyph_2x2=Surface("☺ \n/\\", fg_color=Color(255, 0, 0)),
    glyph_4x2=Surface("o_o]\n/||\\", fg_color=Color(255, 0, 0)),
)

DEAD_RED_GLADIATOR_TEXTURE = Texture(
    glyph_1x1=Surface("%", fg_color=Color(255, 0, 0)),
    glyph_2x1=Surface("% ", fg_color=Color(255, 0, 0)),
    glyph_2x2=Surface("% \n/\\", fg_color=Color(255, 0, 0)),
    glyph_4x2=Surface("x_x]\n/||\\", fg_color=Color(255, 0, 0)),
)

BLUE_GLADIATOR_TEXTURE = Texture(
    glyph_1x1=Surface("☺", fg_color=Color(0, 0, 255)),
    glyph_2x1=Surface("☺ ", fg_color=Color(0, 0, 255)),
    glyph_2x2=Surface("☺ \n/\\", fg_color=Color(0, 0, 255)),
    glyph_4x2=Surface("o_o]\n/||\\", fg_color=Color(0, 0, 255)),
)

DEAD_BLUE_GLADIATOR_TEXTURE = Texture(
    glyph_1x1=Surface("%", fg_color=Color(0, 0, 255)),
    glyph_2x1=Surface("% ", fg_color=Color(0, 0, 255)),
    glyph_2x2=Surface("% \n/\\", fg_color=Color(0, 0, 255)),
    glyph_4x2=Surface("x_x]\n/||\\", fg_color=Color(0, 0, 255)),
)

"""
◑  ◐
//\\\\

▆▂▂▆ 
▊ε ▊

▆▂▂▆
▊▽ ▊

▆▂▂▆
╳◠ ╳

◭▽ ◮
┑__┎

◭▽ ◮
┑◟◞┎
"""
