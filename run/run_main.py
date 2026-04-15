import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_PATH = BASE_DIR / "main.py"

os.startfile(APP_PATH)