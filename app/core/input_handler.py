from pynput import keyboard
from queue import Queue


class InputHandler:
    def __init__(self):
        self.event_queue = Queue()
        self.keys_pressed = set()
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )

    def start(self):
        self.listener.start()

    def stop(self):
        self.listener.stop()
        self.listener.join()

    def on_press(self, key):
        self.event_queue.put(("press", key))

    def on_release(self, key):
        self.event_queue.put(("release", key))

    def update(self):
        while not self.event_queue.empty():
            event_type, key = self.event_queue.get()
            if event_type == "press":
                self.keys_pressed.add(key)
            elif event_type == "release":
                self.keys_pressed.discard(key)

    def get_keys_pressed(self):
        return self.keys_pressed.copy()
