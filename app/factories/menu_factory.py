from app.states.menu import Menu, MenuItem
from app.core import NavigationContext


def create_menu_factory(animation_factories):
    def menu_factory(context: NavigationContext):
        def create_demo_menu():
            return Menu(
                context,
                "Demo menu",
                [
                    MenuItem(
                        animation_factory.name,
                        lambda animation_factory=animation_factory:
                        context.push_state_factory(animation_factory)
                    )
                    for animation_factory in animation_factories
                ] + [
                    MenuItem("Back", context.pop_state)
                ]
            )

        main_menu = Menu(
            context,
            "Main menu",
            [
                MenuItem(
                    "Demo menu",
                    lambda: context.push_state(create_demo_menu())
                ),
                MenuItem("Exit", context.stop)
            ]
        )

        return main_menu

    menu_factory.context_type = NavigationContext
    return menu_factory
