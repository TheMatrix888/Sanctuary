from app.core import App, InputHandler
from app.states.animation import create_animations
from app.states.menu import create_menus
from engine.screen import Screen

input_handler = InputHandler()
input_handler.start()

screen = Screen(400, 400, 40, 20)

app = App(input_handler, screen)
animations = create_animations(app)
menu = create_menus(app, animations)
app.push_state(menu)

try:
    while app.running:
        input_handler.update()
        state = app.current_state
        state.handle_input()
        state.update()
        state.render()

except KeyboardInterrupt:
    app.stop()

finally:
    input_handler.stop()
