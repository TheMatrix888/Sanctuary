"""
Multi-resolution Texture assets for the tactical arena.
Decouples visual Surface representations entirely from physical tile material properties.
"""
from dataclasses import dataclass

from sanctuary.core.primitives import Color, Surface


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

    def with_color(self, fg_color: Color | None = None, bg_color: Color | None = None) -> "Texture":
        """Returns a new Texture with the specified colors applied across all footprint Surfaces."""
        return Texture(
            glyph_1x1=self.glyph_1x1.with_color(fg_color, bg_color),
            glyph_2x1=self.glyph_2x1.with_color(fg_color, bg_color),
            glyph_2x2=self.glyph_2x2.with_color(fg_color, bg_color),
            glyph_4x2=self.glyph_4x2.with_color(fg_color, bg_color),
        )


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

# Base gladiator template assets (neutral / uncolored)
GLADIATOR_TEXTURE = Texture(
    glyph_1x1=Surface("☺"),
    glyph_2x1=Surface("☺ "),
    glyph_2x2=Surface("☺ \n/\\"),
    glyph_4x2=Surface("o_o]\n/||\\"),
)

DEAD_GLADIATOR_TEXTURE = Texture(
    glyph_1x1=Surface("%"),
    glyph_2x1=Surface("% "),
    glyph_2x2=Surface("% \n/\\"),
    glyph_4x2=Surface("x_x]\n/||\\"),
)

PLAYER_TEXTURE = GLADIATOR_TEXTURE.with_color(Color(128, 0, 255))

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
