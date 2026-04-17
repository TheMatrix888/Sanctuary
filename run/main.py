from app.core import App, InputHandler
from app.states.animation import create_animations
from app.states.menu import create_menus
from engine.screen import Screen
from time import time, sleep

input_handler = InputHandler()
input_handler.start()

screen = Screen((400, 400), 40, 20)

app = App(input_handler, screen)

# State creation
animations = create_animations(app)
main_menu = create_menus(app, animations)

app.push_state(main_menu)

try:
    target_ups = 60
    update_time = 1/target_ups
    while app.running:
        start = time()

        input_handler.update()
        state = app.current_state
        state.handle_input()
        state.update()
        state.render()

        elapsed = time() - start
        sleep_time = max(0.0, update_time - elapsed)
        sleep(sleep_time)

except KeyboardInterrupt:
    app.stop()

finally:
    input_handler.stop()
