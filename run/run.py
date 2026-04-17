import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_PATH = BASE_DIR / "main.py"

subprocess.Popen(
    [sys.executable, str(APP_PATH)],
    creationflags=subprocess.CREATE_NEW_CONSOLE
)