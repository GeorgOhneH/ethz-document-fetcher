import os
from pathlib import Path

SEPARATOR = ":="
FOLDER_PATH = os.path.dirname(__file__)
ROOT_PATH = os.path.dirname(FOLDER_PATH)
CONFIG_PATH = os.path.join(ROOT_PATH, "config")
Path(CONFIG_PATH).mkdir(parents=True, exist_ok=True)
