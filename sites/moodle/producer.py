from bs4 import BeautifulSoup

from core.constants import BEAUTIFUL_SOUP_PARSER
from core.exceptions import LoginError
from sites.moodle.parser import parse_main_page
from .constants import AUTH_URL


async def producer(session, queue, base_path, id, use_external_links=True):
    async with session.get(f"https://moodle-app2.let.ethz.ch/course/view.php?id={id}") as response:
        html = await response.read()
        if str(response.url) == AUTH_URL:
            raise LoginError("Module moodle isn't logged in")
    return await parse_main_page(session, queue, html, base_path, id, use_external_links)


async def get_folder_name(session, id, **kwargs):
    async with session.get(f"https://moodle-app2.let.ethz.ch/course/view.php?id={id}") as response:
        html = await response.read()
    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

    header = soup.find("div", class_="page-header-headings")
    header_name = str(header.h1.string)
    return header_name
