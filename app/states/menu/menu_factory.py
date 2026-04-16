from .menu import Menu
from .menu_item import MenuItem


def create_menus(app, animations):
    main_menu = Menu(app, "Main menu",
                     [
                         MenuItem("Demo menu", lambda: app.push_state(demo_menu)),
                         MenuItem("Exit", lambda: app.stop())
                     ])
    # Demo menu creation

    demo_menu = Menu(app, "Demo menu",
                     [
                         MenuItem(animation.name, lambda: app.push_state(animation)) for animation in animations
                     ]
                     + [MenuItem("Back", lambda: app.pop_state())]
                     )
    return main_menu
