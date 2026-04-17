from app.core import State
from .menu_item import MenuItem
from engine.screen_objects import ScreenObject


class Menu(State):
    def __init__(self, app, name: str, items: list[MenuItem], cycle_pointer=False):
        super().__init__(app)
        self.pointer = 0
        self.name = name
        self.items = items
        self.cycle_pointer = cycle_pointer

    def on_enter(self):
        self.status_bar.set_segment("menu", self.name)
        self.status_bar.layout(self.screen.columns)
        self.screen.place(self.status_bar, "bottom_left")

    def on_exit(self):
        self.pointer = 0
        self.status_bar.pop_segment("menu")

    def handle_input(self):
        input_handler = self.input_handler
        if not input_handler.idle:
            if input_handler.is_pressed("up"):
                self.up()
            elif input_handler.is_pressed("down"):
                self.down()
            elif input_handler.is_pressed("enter"):
                self.select()

    def update(self):
        pass

    def render(self):
        screen_object = ScreenObject((0, 0))
        content = []
        for i, item in enumerate(self.items):
            line = f"{i + 1}." + item.label
            if i == self.pointer:
                line += "<--"
            content.append(line)
        screen_object.set_content(content)
        self.screen.clear()
        self.screen.draw(screen_object)
        self.screen.draw(self.status_bar)
        self.screen.update()

    def up(self):
        self.pointer -= 1
        if self.pointer <= 0:
            if self.cycle_pointer:
                self.pointer = len(self.items) - 1
            else:
                self.pointer = 0

    def down(self):
        self.pointer += 1
        if self.pointer >= len(self.items):
            if self.cycle_pointer:
                self.pointer = 0
            else:
                self.pointer -= 1

    def select(self):
        self.items[self.pointer].execute()
