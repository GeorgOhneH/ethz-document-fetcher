import os

GUI_PATH = os.path.dirname(__file__)

ROOT_PATH = os.path.dirname(GUI_PATH)

ASSETS_PATH = os.path.join(GUI_PATH, "assets")

SITE_ICON_PATH = os.path.join(ASSETS_PATH, "site_icons")

TUTORIAL_URL = "https://github.com/GeorgOhneH/ethz-document-fetcher/blob/master/TUTORIAL.md"

THEME_NATIVE = "Native"
THEME_FUSION_DARK = "Fusion Dark"
THEME_FUSION_LIGHT = "Fusion Light"
DARK_THEMES = {THEME_FUSION_DARK}
LIGHT_THEMES = {THEME_NATIVE, THEME_FUSION_LIGHT}
ALL_THEMES = [THEME_NATIVE, THEME_FUSION_DARK, THEME_FUSION_LIGHT]  # Order matters
