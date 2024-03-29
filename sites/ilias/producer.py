import asyncio
import datetime
import re

import aiohttp
from babel.dates import format_datetime
from bs4 import BeautifulSoup, SoupStrainer

from core.exceptions import LoginError
from core.utils import get_beautiful_soup_parser, safe_path_join
from settings.config import ConfigString
from sites.ilias import login
from sites.ilias.constants import GOTO_URL
from sites.utils import remove_vz_id

ILIAS_ID_CONFIG = ConfigString(gui_name="ID")


async def get_folder_name(session, ilias_id, **kwargs):
    url = GOTO_URL + str(ilias_id)
    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, get_beautiful_soup_parser())

    ol = soup.find("ol", class_="breadcrumb")
    name = str(ol.find_all("li")[2].string)
    return remove_vz_id(name)


async def producer(session, queue, base_path, download_settings, ilias_id: ILIAS_ID_CONFIG):
    await search_tree(session, queue, base_path, download_settings, ilias_id)


async def search_tree(session, queue, base_path, download_settings, ilias_id):
    url = GOTO_URL + str(ilias_id)
    async with session.get(url) as response:
        html = await response.text()
        if str(response.url) != url:
            raise LoginError("Module ilias isn't logged in or you are not allowed to access these files")

    strainer = SoupStrainer("div", attrs={"class": "ilCLI ilObjListRow row"})
    soup = BeautifulSoup(html, get_beautiful_soup_parser(), parse_only=strainer)
    rows = soup.find_all("div", attrs={"class": "ilCLI ilObjListRow row"})
    tasks = []
    for row in rows:
        content = row.find("div", attrs={"class": "ilContainerListItemContent"})
        link = content.find("a")
        href = link["href"]
        name = str(link.string)
        path = safe_path_join(base_path, name)
        if "download" in href:
            extension = str(content.find("span", attrs={"class": "il_ItemProperty"}).string).strip()
            checksum = "".join([str(x.string).strip() for x in
                                content.find_all("span", attrs={"class": "il_ItemProperty"})])

            if "Today" in checksum:
                today_date = datetime.datetime.now()
                checksum = checksum.replace("Today", format_datetime(today_date,
                                                                     locale='en',
                                                                     format="dd. MMM YYYY"))
            elif "Yesterday" in checksum:
                yesterday_date = datetime.datetime.now() - datetime.timedelta(days=1)
                checksum = checksum.replace("Yesterday", format_datetime(yesterday_date,
                                                                         locale='en',
                                                                         format="dd. MMM YYYY"))

            await queue.put({"url": href, "path": f"{path}.{extension}", "checksum": checksum})
        else:
            ref_id = re.search("ref_id=([0-9]+)&", href).group(1)
            coroutine = search_tree(session, queue, path, download_settings, ref_id)
            tasks.append(asyncio.ensure_future(coroutine))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    async def main():
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            await login(session)
            await get_folder_name(session, "187834")


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
