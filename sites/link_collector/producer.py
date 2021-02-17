import os
import re
from urllib.parse import urlparse, urlunparse, urljoin

from bs4 import BeautifulSoup
from aiohttp import BasicAuth

from core.utils import safe_path_join, get_beautiful_soup_parser

from sites.standard_config_objs import BASIC_AUTH_CONFIG, HEADERS_CONFIG,\
    basic_auth_config_to_session_kwargs, headers_config_to_session_kwargs

from settings.config_objs import ConfigList, ConfigDict, ConfigString, ConfigBool

REGEX_PATTERN_CONFIG = ConfigList(
    gui_name="Regex Patterns",
    hint_text="This uses the <a href=\"https://docs.python.org/3/library/re.html#re.sub\">re.sub</a>"
              " function. The replacements<br>are 'Folder Name' and 'File Name'",
    config_obj_default=ConfigDict(
        gui_name="Filter",
        layout={
            "pattern": ConfigString(
                gui_name="Pattern"
            ),
            "folder": ConfigString(
                gui_name="Folder Name",
                optional=True,
            ),
            "file_name": ConfigString(
                gui_name="File Name",
                optional=True,
                hint_text="<name> will be replaced with the link name from the website.",
            )
        }
    )
)

URL_CONFIG = ConfigString(gui_name="Url")


async def producer(session,
                   queue,
                   base_path,
                   site_settings,
                   url: URL_CONFIG,
                   regex_patterns: REGEX_PATTERN_CONFIG,
                   headers: HEADERS_CONFIG,
                   basic_auth: BASIC_AUTH_CONFIG):
    session_kwargs = headers_config_to_session_kwargs(headers)

    session_kwargs.update(basic_auth_config_to_session_kwargs(basic_auth, site_settings))

    links = await get_all_file_links(session, url, session_kwargs)
    for regex_pattern in regex_patterns:
        pattern = regex_pattern["pattern"]
        folder_regex = regex_pattern["folder"]
        if folder_regex is None:
            folder_regex = ""
        file_name_regex = regex_pattern["file_name"]
        for link, html_name in links:

            if re.search(pattern, link) is None:
                continue

            folder_name = re.sub(pattern, folder_regex, link)

            o = urlparse(link)

            file_name = _get_file_name(url_file_name=o.path.split("/")[-1],
                                       html_name=html_name,
                                       file_name_regex=file_name_regex,
                                       pattern=pattern,
                                       link=link)

            await queue.put({
                "url": link,
                "path": safe_path_join(base_path, folder_name, file_name),
                "session_kwargs": session_kwargs,
            })


def _get_file_name(url_file_name: str,
                   html_name: str,
                   pattern: str,
                   link: str,
                   file_name_regex: str) -> str:

    extension = url_file_name.split(".")[-1]

    if file_name_regex:
        modified_file_name_regex = file_name_regex.replace("<name>", html_name)
        file_name = re.sub(pattern, modified_file_name_regex, link)
        if not file_name.endswith("." + extension):
            file_name += f".{extension}"
        return file_name

    if html_name:
        if html_name.endswith("." + extension):
            return html_name
        return f"{html_name}.{extension}"

    return url_file_name


async def get_all_file_links(session, url, session_kwargs):
    async with session.get(url, **session_kwargs) as response:
        html = await response.text()

    all_links = set([])

    soup = BeautifulSoup(html, get_beautiful_soup_parser())

    links = soup.find_all("a")
    for link in links:
        href = link.get("href", None)
        if not href:
            continue

        o = urlparse(href)

        if "." not in o.path:
            continue

        result = urljoin(url, href)

        all_links.add((result, str(link.string)))

    return all_links


async def get_folder_name(session, url, **kwargs):
    async with session.get(url) as response:
        html = await response.text()
    soup = BeautifulSoup(html, get_beautiful_soup_parser())
    title = soup.find("title")

    return str(title.string)
