from time import time, sleep

from run.logger import logger_init
from app.input import InputHandler
from app.core import App
from app.factories import create_animation_factories, create_menu_factory

from engine.primitives import pos, size
from engine.screen import Screen

import sys
import subprocess


def run_new_console():
    subprocess.Popen(
        [sys.executable, "-m", "run.main", "--child"],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )


def main():
    if "--new-console" in sys.argv:
        run_new_console()
        return

    run_app()


def run_app():
    logger_init()

    input_handler = InputHandler()
    input_handler.start()

    screen = Screen(pos(400, 400), size(40, 20))
    app = App(input_handler, screen)

    animation_factories = create_animation_factories()
    menu_factory = create_menu_factory(animation_factories)

    app.push_state_factory(menu_factory)

    try:
        target_ups = 60
        update_time = 1 / target_ups

        while app.running:
            start = time()

            input_handler.update()

            state = app.current_state
            state.handle_input()
            state.update()

            screen.clear()
            state.render()
            app.render_status_bar()
            screen.update()

            elapsed = time() - start
            sleep(max(0.0, update_time - elapsed))

    finally:
        input_handler.stop()


if __name__ == "__main__":
    main()
