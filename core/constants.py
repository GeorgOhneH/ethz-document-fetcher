import logging

import bs4
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

try:
    BeautifulSoup("", "lxml")
    BEAUTIFUL_SOUP_PARSER = "lxml"
except bs4.FeatureNotFound:
    logger.warning("It appears that 'lxml' is not installed. Falling back to 'html.parser'")
    BEAUTIFUL_SOUP_PARSER = "html.parser"

FORCE_DOWNLOAD_BLACKLIST = ["ilias-app2.let.ethz.ch", "polybox.ethz.ch"]

MOVIE_EXTENSIONS = ["mp4", "webm", "avi", "mkv", "mov", "m4v"]
ACTION_NEW = 0
ACTION_REPLACE = 1

