import bs4
from bs4 import BeautifulSoup

import logging

logger = logging.getLogger(__name__)

try:
    BeautifulSoup("", "lxml")
    BEAUTIFUL_SOUP_PARSER = "lxml"
except bs4.FeatureNotFound:
    logger.warning("It appears that 'lxml' is not installed. Falling back to 'html.parser'")
    BEAUTIFUL_SOUP_PARSER = "html.parser"
