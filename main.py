"""
Sanctuary Main Entrypoint — Application Lifecycle Bootstrap.
Initializes the host platform, binds the Screen, instantiates the Menu,
and enters the canonical 60 FPS State Stack game loop.
"""
import sys
import traceback

from sanctuary.core.app import App
from sanctuary.core.platform import create_platform
from sanctuary.scenes.menu import create_main_menu


def main() -> None:
    """Main application lifecycle entrypoint."""
    platform = create_platform()

    app = App(platform)
    main_menu = create_main_menu()

    app.push_state(main_menu)
    app.run()


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        error_trace = traceback.format_exc()
        try:
            with open("crash.log", "w", encoding="utf-8") as file:
                file.write(error_trace)
        except Exception:
            pass

        print("\n" + "=" * 50)
        print("CRITICAL EXCEPTION (saved to crash.log):")
        print("=" * 50)
        print(error_trace, end="")
        print("=" * 50)

        try:
            import msvcrt
            # Drain buffered keystrokes (such as Enter pressed right before the crash)
            while msvcrt.kbhit():
                msvcrt.getch()
            print("\nPress any key to exit...")
            msvcrt.getch()
        except ImportError:
            input("\nPress enter to exit...")
        sys.exit(1)

