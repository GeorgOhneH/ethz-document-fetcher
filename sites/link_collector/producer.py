import os
import re
from urllib.parse import urlparse, urlunparse, urljoin

from bs4 import BeautifulSoup

from core.constants import BEAUTIFUL_SOUP_PARSER
from core.utils import safe_path_join

from settings.config_objs import ConfigList, ConfigDict, ConfigString, ConfigPath

regrex_pattern_config = ConfigList(
    gui_name="Regrex Patterns",
    hint_text="This uses the <a href=\"https://docs.python.org/3/library/re.html#re.sub\">re.sub</a>"
              " function. The replacements are 'Folder Name' and 'File Name'",
    config_obj_default=ConfigDict(
        gui_name="",
        layout={
            "pattern": ConfigString(
                gui_name="Pattern"
            ),
            "folder": ConfigString(
                gui_name="Folder Name"
            ),
            "file_name": ConfigString(
                gui_name="File Name",
                optional=True
            )
        }
    )
)


async def producer(session,
                   queue,
                   base_path,
                   site_settings,
                   url,
                   regrex_patterns: regrex_pattern_config):
    links = await get_all_file_links(session, url)
    for regrex_pattern in regrex_patterns:
        pattern = regrex_pattern["pattern"]
        folder_regrex = regrex_pattern["folder"]
        file_name_regrex = regrex_pattern["file_name"]
        for link, name in links:

            if re.search(pattern, link) is None:
                continue

            folder_name = re.sub(pattern, folder_regrex, link)

            o = urlparse(link)

            file_name = o.path.split("/")[-1]
            extension = file_name.split(".")[-1]

            if name:
                file_name = f"{name}.{extension}"

            if file_name_regrex:
                user_file_name = re.sub(pattern, file_name_regrex, link)
                if "." not in user_file_name:
                    user_file_name += f".{extension}"
                file_name = user_file_name

            await queue.put({"url": link, "path": safe_path_join(base_path, folder_name, file_name)})


async def get_all_file_links(session, url):
    async with session.get(url) as response:
        html = await response.text()

    all_links = set([])

    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

    links = soup.find_all("a")
    for link in links:
        href = link.get("href", None)
        if not href:
            continue

        o = urlparse(href)

        if "." not in o.path:
            continue

        result = urljoin(url, href)

        all_links.add((result, link.string))

    return all_links


async def get_folder_name(session, url, **kwargs):
    async with session.get(url) as response:
        html = await response.text()
    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)
    title = soup.find("title")

    return title.string
