"""
Multi-resolution Texture assets for the tactical arena.
Decouples visual Surface representations entirely from physical tile material properties.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sanctuary.core.primitives import Color, Surface

if TYPE_CHECKING:
    from sanctuary.core.screen import Screen


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


# =============================================================================
# SELECTION & FRAMING TEXTURES
# =============================================================================

@dataclass(slots=True, frozen=True)
class SelectionTexture:
    """
    Multi-resolution framing texture designed to bracket an arena cell.
    Surrounds cell contents with +1 column margin on both left and right sides:
    - 1x1 cell -> 3x1 surface  ('[ ]')
    - 2x1 cell -> 4x1 surface  ('[  ]')
    - 2x2 cell -> 4x2 surface  ('[  ]\\n[  ]')
    - 4x2 cell -> 6x2 surface  ('[    ]\\n[    ]')
    """
    frame_1x1: Surface
    frame_2x1: Surface
    frame_2x2: Surface
    frame_4x2: Surface

    def get_surface(self, scale: tuple[int, int] = (1, 1)) -> Surface:
        """Retrieves the corresponding Surface for the target footprint scale."""
        if scale == (4, 2):
            return self.frame_4x2
        if scale == (2, 2):
            return self.frame_2x2
        if scale == (2, 1):
            return self.frame_2x1
        return self.frame_1x1

    def with_color(self, fg_color: Color | None = None, bg_color: Color | None = None) -> "SelectionTexture":
        """Returns a new SelectionTexture with the specified colors applied across all Surfaces."""
        return SelectionTexture(
            frame_1x1=self.frame_1x1.with_color(fg_color, bg_color),
            frame_2x1=self.frame_2x1.with_color(fg_color, bg_color),
            frame_2x2=self.frame_2x2.with_color(fg_color, bg_color),
            frame_4x2=self.frame_4x2.with_color(fg_color, bg_color),
        )

    def draw(
        self,
        screen: "Screen",
        origin_x: int,
        origin_y: int,
        tile_x: int,
        tile_y: int,
        scale: tuple[int, int] = (1, 1),
    ) -> None:
        """
        Renders the selection frame centered over the target tile, automatically
        applying the -1 X column offset so brackets flank the cell cleanly.
        """
        scale_w, scale_h = scale
        screen_x = origin_x + tile_x * scale_w - 1
        screen_y = origin_y + tile_y * scale_h
        surface = self.get_surface(scale)
        screen.draw_surface(screen_x, screen_y, surface, transparent_space=True)


RETICLE_BASE_TEXTURE = SelectionTexture(
    frame_1x1=Surface("[ ]"),
    frame_2x1=Surface("[  ]"),
    frame_2x2=Surface("┌  ┐\n└  ┘"),
    frame_4x2=Surface("┌    ┐\n└    ┘"),
)

RETICLE_AMBER_TEXTURE = RETICLE_BASE_TEXTURE.with_color(Color(255, 190, 40))
RETICLE_RED_TEXTURE = RETICLE_BASE_TEXTURE.with_color(Color(255, 60, 60))


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
