from .state import State


class App:
    def __init__(self):
        self.running = True
        self.state_stack = []

    def push_state(self, state: State):
        self.state_stack.append(state)
        state.on_enter()

    def pop_state(self):
        if self.state_stack:
            state = self.state_stack.pop()
            state.on_exit()

    @property
    def current_state(self) -> State:
        return self.state_stack[-1]

    def stop(self):
        while self.state_stack:
            state = self.state_stack.pop()
            state.on_exit()
        self.running = False
