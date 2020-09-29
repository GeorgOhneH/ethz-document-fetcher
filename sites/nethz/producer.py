import asyncio
import re

from bs4 import BeautifulSoup

from core.constants import BEAUTIFUL_SOUP_PARSER
from core.utils import safe_path_join

from sites.standard_config_objs import BASIC_AUTH_CONFIG, basic_auth_config_to_session_kwargs


async def get_folder_name(session, url, **kwargs):
    async with session.get(url) as response:
        html = await response.text()
    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

    header_name = str(soup.head.title.string)
    name = re.search("/~([^/]+)/", header_name)[1]

    return name


async def producer(session, queue, url, base_path, site_settings, basic_auth: BASIC_AUTH_CONFIG):
    session_kwargs = basic_auth_config_to_session_kwargs(basic_auth, site_settings)
    await _producer(session, queue, url, base_path, session_kwargs)


async def _producer(session, queue, url, base_path, session_kwargs):
    if url[-1] != "/":
        url += "/"

    async with session.get(url, **session_kwargs) as response:
        html = await response.text()

    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

    links = soup.find_all("a")
    tasks = []
    for link in links:
        href = link.get("href")
        if href != str(link.string).strip():
            continue

        if href[-1] == "/":
            href = href[:-1]

        path = safe_path_join(base_path, href)

        if "." in href:
            checksum = str(link.next_sibling.string).strip()
            await queue.put({"url": url + href,
                             "path": path,
                             "session_kwargs": session_kwargs,
                             "checksum": checksum})
        else:
            coroutine = _producer(session, queue, url + href, path, session_kwargs)
            tasks.append(asyncio.ensure_future(coroutine))

    await asyncio.gather(*tasks)
