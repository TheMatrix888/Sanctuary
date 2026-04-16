from .menu import Menu
from .menu_item import MenuItem


def create_menus(app, animations):
    main_menu = Menu(app, "Main menu",
                     [
                         MenuItem("Demo menu", lambda: app.push_state(demo_menu)),
                         MenuItem("Exit", lambda: app.stop())
                     ])
    demo_menu = Menu(app, "Demo menu",
                       [
                           MenuItem("Demo animation 0", lambda: None),
                           MenuItem("Back", lambda: app.pop_state()),
                       ])
    return main_menu
