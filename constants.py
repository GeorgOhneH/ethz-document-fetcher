import os
from pathlib import Path

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

MOVIE_EXTENSIONS = ["mp4", "webm", "avi", "mkv", "mov", "m4v"]

CACHE_PATH = os.path.join(os.path.dirname(__file__), "cache")
Path(CACHE_PATH).mkdir(parents=True, exist_ok=True)
