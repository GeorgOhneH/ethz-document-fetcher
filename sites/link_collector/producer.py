import os
import re
from urllib.parse import urlparse, urlunparse, urljoin

from bs4 import BeautifulSoup
from aiohttp import BasicAuth

from core.utils import safe_path_join, get_beautiful_soup_parser

from sites.standard_config_objs import BASIC_AUTH_CONFIG, HEADERS_CONFIG, \
    basic_auth_config_to_session_kwargs, headers_config_to_session_kwargs

from settings.config_objs import ConfigList, ConfigDict, ConfigString, ConfigBool

REGEX_PATTERN_CONFIG = ConfigList(
    gui_name="Regex Patterns",
    hint_text="This uses the <a href=\"https://docs.python.org/3/library/re.html#re.sub\">re.sub</a>"
              " function. The replacements<br>are 'Folder Name', 'File Name' and 'Link Modifier'",
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
            ),
            "link_regex": ConfigString(
                gui_name="Link Modifier",
                optional=True,
            ),
        }
    )
)

URL_CONFIG = ConfigString(gui_name="Url")


async def producer(session,
                   queue,
                   base_path,
                   download_settings,
                   url: URL_CONFIG,
                   regex_patterns: REGEX_PATTERN_CONFIG,
                   headers: HEADERS_CONFIG,
                   basic_auth: BASIC_AUTH_CONFIG):
    session_kwargs = headers_config_to_session_kwargs(headers)

    session_kwargs.update(basic_auth_config_to_session_kwargs(basic_auth, download_settings))

    if url and url[-1] != "/" and "." not in url.split("/")[-1]:
        url += "/"

    links = await get_all_file_links(session, url, session_kwargs)
    for regex_pattern in regex_patterns:
        pattern = regex_pattern["pattern"]
        folder_regex = regex_pattern.get("folder", None)
        link_regex = regex_pattern.get("link_regex", None)
        if folder_regex is None:
            folder_regex = ""
        file_name_regex = regex_pattern.get("file_name", None)
        for link, html_name in links.items():

            if re.search(pattern, link) is None:
                continue

            folder_name = re.sub(pattern, folder_regex, link)

            o = urlparse(link)

            file_name = _get_file_name(url_file_name=o.path.split("/")[-1],
                                       html_name=html_name,
                                       file_name_regex=file_name_regex,
                                       pattern=pattern,
                                       link=link)

            if link_regex:
                link = re.sub(pattern, link_regex, link)

            await queue.put({
                "url": link,
                "path": safe_path_join(base_path, folder_name, file_name),
                "session_kwargs": session_kwargs,
                "with_extension": "." in file_name,
            })


def _get_file_name(url_file_name: str or bytes,
                   html_name: str,
                   pattern: str,
                   link: str,
                   file_name_regex: str) -> (str, bool):
    if file_name_regex:
        modified_file_name_regex = file_name_regex.replace("<name>", html_name)
        file_name = re.sub(pattern, modified_file_name_regex, link)
    elif html_name:
        file_name = html_name
    else:
        file_name = url_file_name

    if "." in file_name:
        # This is not 100% correct. A file still can not have a extension,
        # but I think it should be fine, because the user can always explicit add an extension
        return file_name
    if "." in url_file_name:
        default_extension = url_file_name.split(".")[-1]
        file_name += f".{default_extension}"
        return file_name
    return file_name  # Has no extension


async def get_all_file_links(session, url, session_kwargs):
    async with session.get(url, **session_kwargs) as response:
        html = await response.text()

    all_links = dict()

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

        all_links[result] = str(link.text)

    return all_links


async def get_folder_name(session, url, **kwargs):
    async with session.get(url) as response:
        html = await response.text()
    soup = BeautifulSoup(html, get_beautiful_soup_parser())
    title = soup.find("title")

    return str(title.string)
