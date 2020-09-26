import os
import re
from urllib.parse import urlparse, urlunparse, urljoin

from bs4 import BeautifulSoup
from aiohttp import BasicAuth

from core.constants import BEAUTIFUL_SOUP_PARSER
from core.utils import safe_path_join

from settings.config_objs import ConfigList, ConfigDict, ConfigString, ConfigBool

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
                gui_name="Folder Name",
                optional=True,
            ),
            "file_name": ConfigString(
                gui_name="File Name",
                optional=True,
                hint_text="<name> will be replaced with the file name from the website.",
            )
        }
    )
)

headers_config = ConfigList(
    gui_name="Headers",
    hint_text="This is only useful if you want to add your own headers",
    optional=True,
    config_obj_default=ConfigDict(
        gui_name="",
        layout={
            "key": ConfigString(
                gui_name="Key",
                optional=True,
            ),
            "value": ConfigString(
                gui_name="Value",
                optional=True,
            ),
        }
    )
)


def basic_auth_config_use_eth_credentials(instance, from_widget, parent):
    if from_widget:
        use = parent.get_from_widget()["use"]
    else:
        use = parent.get()["use"]
    return use


def basic_auth_config_custom(instance, from_widget, parent):
    if from_widget:
        use_eth_credentials = parent.get_from_widget()["use_eth_credentials"]
        use = parent.get_from_widget()["use"]
    else:
        use_eth_credentials = parent.get()["use_eth_credentials"]
        use = parent.get()["use"]
    return not use_eth_credentials and use


basic_auth_config = ConfigDict(
    optional=True,
    gui_name="Basic Authentication",
    layout={
        "use": ConfigBool(default=False, gui_name="Use Basic Authentication"),
        "use_eth_credentials": ConfigBool(default=False,
                                          gui_name="Use ETH Credentials",
                                          gray_out=True,
                                          active_func=basic_auth_config_use_eth_credentials),
        "custom": ConfigDict(
            active_func=basic_auth_config_custom,
            gui_name="Custom",
            gray_out=True,
            layout={
                "username": ConfigString(),
                "password": ConfigString(),
            }
        )
    }
)


async def producer(session,
                   queue,
                   base_path,
                   site_settings,
                   url,
                   regrex_patterns: regrex_pattern_config,
                   headers: headers_config,
                   basic_auth: basic_auth_config):
    headers = {d["key"]: d["value"] for d in headers}
    session_kwargs = {"headers": headers}

    if basic_auth["use"]:
        if basic_auth["use_eth_credentials"]:
            session_kwargs["auth"] = BasicAuth(login=site_settings.username,
                                               password=site_settings.password)
        else:
            session_kwargs["auth"] = BasicAuth(login=basic_auth["custom"]["username"],
                                               password=basic_auth["custom"]["password"])

    links = await get_all_file_links(session, url, session_kwargs)
    for regrex_pattern in regrex_patterns:
        pattern = regrex_pattern["pattern"]
        folder_regrex = regrex_pattern["folder"]
        if folder_regrex is None:
            folder_regrex = ""
        file_name_regrex = regrex_pattern["file_name"]
        for link, html_name in links:

            if re.search(pattern, link) is None:
                continue

            folder_name = re.sub(pattern, folder_regrex, link)

            o = urlparse(link)

            file_name = _get_file_name(url_file_name=o.path.split("/")[-1],
                                       html_name=html_name,
                                       file_name_regrex=file_name_regrex,
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
                   file_name_regrex: str) -> str:

    extension = url_file_name.split(".")[-1]

    if file_name_regrex:
        modified_file_name_regrex = file_name_regrex.replace("<name>", html_name)
        file_name = re.sub(pattern, modified_file_name_regrex, link)
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

        all_links.add((result, str(link.string)))

    return all_links


async def get_folder_name(session, url, **kwargs):
    async with session.get(url) as response:
        html = await response.text()
    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)
    title = soup.find("title")

    return title.string
