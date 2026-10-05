from os import environ

import shutil
import subprocess
import sys
from pathlib import Path


def detect_platform_environment() -> str:
    """Detects execution environment: windows, linux_gui, linux_tty, macos."""
    if sys.platform == "win32":
        return "windows"

    if sys.platform.startswith("linux"):
        is_wayland = bool(environ.get("WAYLAND_DISPLAY"))
        is_x11 = bool(environ.get("DISPLAY"))
        if is_wayland or is_x11:
            return "linux_gui"
        return "linux_tty"

    if sys.platform == "darwin":
        return "macos"

    return "unknown"


def launch() -> None:
    python_executable = sys.executable
    project_root = Path(__file__).resolve().parent
    main_script = project_root / "main.py"

    environment = environ.copy()
    platform = detect_platform_environment()
    environment["PYTHONUTF8"] = "1"  # Force Python UTF-8 Mode to prevent Windows crashes on Cyrillic/ANSI glyphs

    if platform == "windows":
        # Launch python directly into a detached console window
        subprocess.Popen(
            [python_executable, main_script],
            cwd=project_root,
            env=environment,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    elif platform == "linux_gui":
        # Check for installed terminal emulators under Wayland/X11
        terminals = ["alacritty", "kitty", "foot", "x-terminal-emulator", "gnome-terminal", "xterm"]
        found_terminal = next((term for term in terminals if shutil.which(term)), None)

        if found_terminal:
            subprocess.Popen(
                [found_terminal, "-e", python_executable, main_script],
                cwd=project_root,
                env=environment,
            )
        else:
            subprocess.Popen([python_executable, main_script], cwd=project_root, env=environment)
    else:
        # Linux TTY or headless: run directly in the current console stream
        subprocess.Popen([python_executable, main_script], cwd=project_root, env=environment)


if __name__ == "__main__":
    launch()
