from dataclasses import dataclass

from sanctuary.core.input_handler import InputHandler, Key
from sanctuary.core.primitives import Surface, Color
from sanctuary.core.screen import Screen
from sanctuary.core.state import State, Command, Pop, ToggleMetrics

X_SIZE = 41
Y_SIZE = 21


def generate_arena() -> Surface:
    r = 5
    arena = ""
    color_mask = []

    for y in range(Y_SIZE // 2, -Y_SIZE // 2 - Y_SIZE % 2, -1):
        line = ""
        color_line = []
        for x in range(-X_SIZE // 2, X_SIZE // 2 + X_SIZE % 2):
            f = (x ** 2 + y ** 2 * 2 >= r ** 2) and \
                (x % 2 == 0) and (y % 3 != 0) and \
                (X_SIZE // 3 > x > -X_SIZE // 3) and (Y_SIZE // 3 > y > -Y_SIZE // 3)
            if f:
                line += "#"
                color_line.append(Color(192, 192, 192))
            else:
                line += "·"
                color_line.append(Color(64, 200, 64))
        arena += line + "\n"
        color_mask.append(color_line)
    surface = Surface(arena)
    surface.apply_color_mask(color_mask)
    return surface


@dataclass(slots=True)
class Entity:
    x: int
    y: int
    glyph: str
    fg_color: Color | None = None


class Arena(State):
    arena: Surface
    player: Entity

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.arena = generate_arena()
        self.player = Entity(
            x=X_SIZE // 2,
            y=Y_SIZE // 2,
            glyph="☺",
            fg_color=Color(128, 0, 255)
        )

    def on_enter(self):
        self.reset()

    def handle_input(self, input_handler: InputHandler) -> Command | None:
        if input_handler.just_pressed(Key.RIGHT) or input_handler.just_pressed(Key.D):
            self.player.x += 1
        if input_handler.just_pressed(Key.LEFT) or input_handler.just_pressed(Key.A):
            self.player.x -= 1
        if input_handler.just_pressed(Key.UP) or input_handler.just_pressed(Key.W):
            self.player.y -= 1
        if input_handler.just_pressed(Key.DOWN) or input_handler.just_pressed(Key.S):
            self.player.y += 1
        if input_handler.just_pressed(Key.ESC):
            return Pop()
        if input_handler.just_pressed(Key.F3):
            return ToggleMetrics()
        return None

    def draw(self, screen: Screen) -> None:
        screen.draw_surface(screen.size.columns // 2 - self.player.x, screen.size.rows // 2 - self.player.y, self.arena)
        screen.draw_text(screen.size.columns // 2, screen.size.rows // 2, self.player.glyph, self.player.fg_color)
        ui_text = (
            f"x {self.player.x} y {self.player.y}"
        )
        screen.draw_text(0, screen.size.rows - 1, ui_text.ljust(screen.size.columns), bg_color=Color(64, 64, 64))
