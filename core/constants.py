import logging
import os
import sys

import bs4
from PyQt5.QtCore import QStandardPaths
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

if not QStandardPaths.writableLocation(QStandardPaths.AppDataLocation):
    raise ValueError("Could not find a AppData path")

APP_DATA_PATH = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), "eth-document-fetcher")


try:
    BeautifulSoup("", "lxml")
    BEAUTIFUL_SOUP_PARSER = "lxml"
except bs4.FeatureNotFound:
    logger.warning("It appears that 'lxml' is not installed. Falling back to 'html.parser'")
    BEAUTIFUL_SOUP_PARSER = "html.parser"

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    IS_FROZEN = True
else:
    IS_FROZEN = False

FORCE_DOWNLOAD_BLACKLIST = ["ilias-app2.let.ethz.ch",
                            "polybox.ethz.ch",
                            "ssrweb.zoom.us",
                            "docs.google.com",
                            "jamboard.google.com",
                            "drive.google.com"]

MOVIE_EXTENSIONS = {"mp4", "webm", "avi", "mkv", "mov", "m4v"}
ACTION_NEW = 0
ACTION_REPLACE = 1

CORE_PATH = os.path.dirname(__file__)

ROOT_PATH = os.path.dirname(CORE_PATH)

VERSION_FILE_PATH = os.path.join(ROOT_PATH, "version.txt")

with open(VERSION_FILE_PATH) as f:
    VERSION = f.read().strip()

PYU_VERSION = VERSION[1:]

ASSETS_PATH = os.path.join(CORE_PATH, "assets")

EMPTY_TWO_COLUMN_LEFT_PDF_PATH = os.path.join(ASSETS_PATH, "empty_two_column_left.pdf")

