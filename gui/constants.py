import os
from pathlib import Path

from core.constants import APP_DATA_PATH

GUI_PATH = os.path.dirname(__file__)

ROOT_PATH = os.path.dirname(GUI_PATH)

ASSETS_PATH = os.path.join(GUI_PATH, "assets")

EMPTY_FOLDER_PATH = os.path.join(APP_DATA_PATH, "empty_folder")
Path(EMPTY_FOLDER_PATH).mkdir(parents=True, exist_ok=True)

SITE_ICON_PATH = os.path.join(ASSETS_PATH, "site_icons")


def _get_file_paths(path):
    result = []
    for file_name in os.listdir(path):
        sub_path = os.path.join(path, file_name)
        if not os.path.isfile(sub_path):
            result += _get_file_paths(sub_path)
        else:
            result.append(sub_path)
    return result


TEMPLATE_PRESET_FILE_PATHS = _get_file_paths(os.path.join(ROOT_PATH, "templates"))
TEMPLATE_PRESET_FOLDER_PATHS = [os.path.dirname(path) for path in TEMPLATE_PRESET_FILE_PATHS]

THEME_NATIVE = "Native"
THEME_FUSION_DARK = "Fusion Dark"
THEME_FUSION_LIGHT = "Fusion Light"
DARK_THEMES = {THEME_FUSION_DARK}
LIGHT_THEMES = {THEME_NATIVE, THEME_FUSION_LIGHT}
ALL_THEMES = [THEME_NATIVE, THEME_FUSION_DARK, THEME_FUSION_LIGHT]  # Order matters
