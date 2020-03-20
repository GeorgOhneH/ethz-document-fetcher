from bs4 import BeautifulSoup
import bs4

try:
    BeautifulSoup("", "lxml")
    BEAUTIFUL_SOUP_PARSER = "lxml"
except bs4.FeatureNotFound:
    BeautifulSoup("", "html.parser")
    BEAUTIFUL_SOUP_PARSER = "html.parser"
