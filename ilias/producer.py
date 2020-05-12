import asyncio

import aiohttp
from bs4 import SoupStrainer

from core.constants import *
from core.exceptions import LoginError
from core.utils import *
from ilias.constants import *
from ilias.login import login


async def get_folder_name(session, id):
    url = GOTO_URL + str(id)
    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

    ol = soup.find("ol", class_="breadcrumb")
    return str(ol.find_all("li")[2].string)


async def producer(session, queue, base_path, id):
    await search_tree(session, queue, base_path, id)


async def search_tree(session, queue, base_path, fold_id):
    url = GOTO_URL + str(fold_id)
    async with session.get(url) as response:
        html = await response.text()
        if str(response.url) != url:
            raise LoginError("Module ilias isn't logged in")

    await asyncio.sleep(0)
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
            await queue.put({"url": href, "path": f"{path}.{extension}", "checksum": checksum})
        else:
            ref_id = re.search("ref_id=([0-9]+)&", href).group(1)
            coroutine = search_tree(session, queue, path, ref_id)
            tasks.append(asyncio.create_task(coroutine))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    async def main():
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            await login(session)
            await get_folder_name(session, "187834")


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
