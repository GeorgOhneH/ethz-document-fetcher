import bs4
from bs4 import BeautifulSoup

try:
    BeautifulSoup("", "lxml")
    BEAUTIFUL_SOUP_PARSER = "lxml"
except bs4.FeatureNotFound:
    BeautifulSoup("", "html.parser")
    BEAUTIFUL_SOUP_PARSER = "html.parser"
