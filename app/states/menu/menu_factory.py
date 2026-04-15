from .menu import Menu
from .menu_item import MenuItem


def create_menus(app):
    main_menu = Menu("Main menu",
                     [
                         MenuItem("Sample menu", lambda: app.push_state(sample_menu)),
                         MenuItem("Item", lambda: None),
                         MenuItem("Exit", lambda: app.stop())
                     ])
    sample_menu = Menu("Sample menu",
                       [
                           MenuItem("Item 1", lambda: None),
                           MenuItem("Item 2", lambda: None),
                           MenuItem("Back", lambda: app.pop_state()),
                       ])
    return main_menu
