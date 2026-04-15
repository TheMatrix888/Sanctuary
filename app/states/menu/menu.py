from app.core import State, InputHandler
from .menu_item import MenuItem
from engine.screen_objects import ScreenObject

from pynput import keyboard
from time import time


class Menu(State):
    def __init__(self, app, name: str, items: list[MenuItem], cycle_pointer=False):
        super().__init__(app)
        self.pointer = 0
        self.cycle_pointer = cycle_pointer
        self.name = name
        self.items = items
        self.last_input = time()

    def on_enter(self):
        pass

    def on_exit(self):
        self.pointer = 0

    def handle_input(self, input_handler: InputHandler):
        keys_pressed = input_handler.get_keys_pressed()
        if keys_pressed and (time() - self.last_input > 0.2):
            if keyboard.Key.up in keys_pressed:
                self.up()
            elif keyboard.Key.down in keys_pressed:
                self.down()
            elif keyboard.Key.enter in keys_pressed:
                self.select()
            self.last_input = time()

    def update(self):
        pass

    def get_screen_objects(self):
        screen_object = ScreenObject(0, 0)
        content = []
        for i, item in enumerate(self.items):
            line = f"{i + 1}." + item.label
            if i == self.pointer:
                line += "<--"
            content.append(line)
        screen_object.update_content(content)
        return [screen_object]

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
