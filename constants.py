import bs4
from bs4 import BeautifulSoup

try:
    BeautifulSoup("", "lxml")
    BEAUTIFUL_SOUP_PARSER = "lxml"
except bs4.FeatureNotFound:
    print("It appears that lxml is not installed. Falling back to html.parser")
    BEAUTIFUL_SOUP_PARSER = "html.parser"
