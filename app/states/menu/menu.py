from app.core import State, MenuContext
from .menu_item import MenuItem
from engine.screen_objects import ScreenObject


class Menu(State):
    def __init__(self, context: MenuContext, name: str, items: list[MenuItem], cycle_pointer=False):
        super().__init__(context)
        self.name = name
        self.pointer = 0
        self.items = items
        self.cycle_pointer = cycle_pointer

        self.status_segment_key = "menu"
        self.status = self.name

    def on_enter(self):
        pass

    def on_exit(self):
        self.pointer = 0

    def handle_input(self):
        input_handler = self.input_handler
        if input_handler.is_pressed("up"):
            self.up()
        elif input_handler.is_pressed("down"):
            self.down()
        elif input_handler.is_pressed("enter"):
            self.select()

    def update(self):
        self.set_status(self.name)

    def render(self):
        content = []
        for i, item in enumerate(self.items):
            line = f"{i + 1}." + item.label
            if i == self.pointer:
                line += "<--"
            content.append(line)
        screen_object = ScreenObject((0, 0), content)
        self.screen.draw(screen_object)

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
