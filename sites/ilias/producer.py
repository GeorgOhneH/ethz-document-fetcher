import asyncio
import datetime
import locale

import aiohttp
from bs4 import SoupStrainer

from core.constants import *
from core.exceptions import LoginError
from core.utils import *
from settings.config import ConfigString
from sites.ilias import login
from sites.ilias.constants import *

ILIAS_ID_CONFIG = ConfigString(gui_name="ID")


async def get_folder_name(session, ilias_id, **kwargs):
    url = GOTO_URL + str(ilias_id)
    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

    ol = soup.find("ol", class_="breadcrumb")
    return str(ol.find_all("li")[2].string)


async def producer(session, queue, base_path, site_settings, ilias_id: ILIAS_ID_CONFIG):
    await search_tree(session, queue, base_path, site_settings, ilias_id)


async def search_tree(session, queue, base_path, site_settings, ilias_id):
    url = GOTO_URL + str(ilias_id)
    async with session.get(url) as response:
        html = await response.text()
        if str(response.url) != url:
            raise LoginError("Module ilias isn't logged in")

    strainer = SoupStrainer("div", attrs={"class": "ilCLI ilObjListRow row"})
    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER, parse_only=strainer)
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

            locale.setlocale(locale.LC_TIME, "en_US.utf8")
            if "Today" in checksum:
                today_date = datetime.datetime.now()
                checksum = checksum.replace("Today", today_date.strftime("%d. %b %Y"))
            elif "Yesterday" in checksum:
                yesterday_date = datetime.datetime.now() - datetime.timedelta(days=1)
                yesterday_date.strftime("%d.%b %Y")
                checksum = checksum.replace("Yesterday", yesterday_date.strftime("%d. %b %Y"))
            locale.setlocale(locale.LC_TIME, "")

            await queue.put({"url": href, "path": f"{path}.{extension}", "checksum": checksum})
        else:
            ref_id = re.search("ref_id=([0-9]+)&", href).group(1)
            coroutine = search_tree(session, queue, path, site_settings, ref_id)
            tasks.append(asyncio.ensure_future(coroutine))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    async def main():
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            await login(session)
            await get_folder_name(session, "187834")


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
