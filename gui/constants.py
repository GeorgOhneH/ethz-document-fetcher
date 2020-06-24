import os
from pathlib import Path

GUI_PATH = os.path.dirname(__file__)

ROOT_PATH = os.path.dirname(GUI_PATH)

ASSETS_PATH = os.path.join(GUI_PATH, "assets")

EMPTY_FOLDER_PATH = os.path.join(ASSETS_PATH, "empty_folder")
Path(EMPTY_FOLDER_PATH).mkdir(parents=True, exist_ok=True)

SITE_ICON_PATH = os.path.join(ASSETS_PATH, "site_icons")
