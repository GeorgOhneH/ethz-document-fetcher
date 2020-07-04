import os
from pathlib import Path

from core import constants

SEPARATOR = ":="
FOLDER_PATH = os.path.dirname(__file__)
ROOT_PATH = os.path.dirname(FOLDER_PATH)
CONFIG_PATH = os.path.join(constants.APP_DATA_PATH, "config")
Path(CONFIG_PATH).mkdir(parents=True, exist_ok=True)
