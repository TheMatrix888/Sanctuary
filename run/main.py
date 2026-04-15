from app.core import App, InputHandler
from app.states.menu import create_menus
from engine.screen import Screen

input_handler = InputHandler()
input_handler.start()

screen = Screen(400, 400, 40, 20)

app = App(input_handler, screen)
app.push_state(create_menus(app))

try:
    while app.running:
        input_handler.update()

        state = app.current_state
        state.handle_input(input_handler)
        state.update()


        screen.clear()

        screen_objects = state.get_screen_objects()
        for screen_object in screen_objects:
            screen.draw(screen_object)

        screen.update()

except KeyboardInterrupt:
    app.stop()

finally:
    input_handler.stop()
