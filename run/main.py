from app.core import App, InputHandler
from app.states.menu import create_menus
from engine.screen import Screen
from engine.screen_objects import ScreenObject

input_handler = InputHandler()
app = App()

try:
    input_handler.start()
    app.push_state(create_menus(app))

    screen = Screen(400, 400, 40, 20)
    status_bar = ScreenObject(0, 19)

    while app.running:
        input_handler.update()

        state = app.current_state
        state.handle_input(input_handler)
        state.update()

        status_bar.update_content([str(input_handler.get_keys_pressed())])

        screen.clear()

        screen_objects = state.get_screen_objects()
        for screen_object in screen_objects:
            screen.draw(screen_object)
        screen.draw(status_bar)

        screen.update()

except KeyboardInterrupt:
    app.stop()

finally:
    input_handler.stop()
