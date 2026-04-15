class MenuItem:
    def __init__(self, label, action):
        self.label = label
        self.action = action

    def execute(self):
        self.action()
