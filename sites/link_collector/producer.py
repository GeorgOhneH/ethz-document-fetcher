import re
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

from core.storage import cache
from core.utils import safe_path_join, get_beautiful_soup_parser, add_extension
from settings.config_objs import ConfigList, ConfigDict, ConfigString
from sites.exceptions import NotSingleFile
from sites.standard_config_objs import BASIC_AUTH_CONFIG, HEADERS_CONFIG, \
    basic_auth_config_to_session_kwargs, headers_config_to_session_kwargs
from sites.utils import process_single_file_url

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
        if folder_regex is None:
            folder_regex = ""
        file_name_regex = regex_pattern.get("file_name", None)
        link_regex = regex_pattern.get("link_regex", None)
        for orig_link, html_name in links.items():

            if re.search(pattern, orig_link) is None:
                continue

            folder_name = re.sub(pattern, folder_regex, orig_link)

            if link_regex:
                link = re.sub(pattern, link_regex, orig_link)
            else:
                link = orig_link

            guess_extension = await cache.check_extension(session, link, session_kwargs=session_kwargs)

            file_name = _get_file_name(guess_extension=guess_extension if guess_extension != "html" else None,
                                       html_name=html_name,
                                       file_name_regex=file_name_regex,
                                       pattern=pattern,
                                       orig_link=orig_link,
                                       link_name=urlparse(link).path.split("/")[-1])

            if guess_extension is None or guess_extension == "html":
                try:
                    await process_single_file_url(session=session,
                                                  queue=queue,
                                                  base_path=safe_path_join(base_path, folder_name),
                                                  download_settings=download_settings,
                                                  url=link,
                                                  name=file_name)
                except NotSingleFile:
                    pass
            else:
                await queue.put({
                    "url": link,
                    "path": safe_path_join(base_path, folder_name, file_name),
                    "session_kwargs": session_kwargs,
                })


def _get_file_name(guess_extension: str,
                   html_name: str,
                   pattern: str,
                   orig_link: str,
                   file_name_regex: str,
                   link_name) -> str:
    if file_name_regex:
        modified_file_name_regex = file_name_regex.replace("<name>", html_name)
        file_name = re.sub(pattern, modified_file_name_regex, orig_link)
    elif html_name:
        file_name = html_name
    else:
        file_name = link_name

    return add_extension(file_name, guess_extension)


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
