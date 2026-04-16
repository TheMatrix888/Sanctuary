from pynput import keyboard
from queue import Queue


class InputHandler:
    KEY_MAP = {
        keyboard.Key.up: "up",
        keyboard.Key.down: "down",
        keyboard.Key.enter: "enter",
        keyboard.Key.esc: "esc"
    }

    def __init__(self):
        self.event_queue = Queue()
        self.prev_keys, self.curr_keys = set(), set()
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

    def normalize_key(self, key):
        if isinstance(key, keyboard.Key):
            return self.KEY_MAP.get(key)

        char = getattr(key, "char", None)
        if char:
            return char.lower()

        return None

    def update(self):
        events = {}
        while not self.event_queue.empty():
            event_type, key = self.event_queue.get()
            key = self.normalize_key(key)

            if key is None:
                continue

            events[key] = event_type

        self.prev_keys = self.curr_keys.copy()
        for key, event_type in events.items():
            if event_type == "press":
                self.curr_keys.add(key)
            elif event_type == "release":
                self.curr_keys.discard(key)

    @property
    def idle(self):
        return not self.curr_keys

    def is_pressed(self, key):
        return key in self.curr_keys and key not in self.prev_keys

    def is_held(self, key):
        return key in self.curr_keys