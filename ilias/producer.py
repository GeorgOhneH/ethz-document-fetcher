import asyncio
import re

import aiohttp

from constants import *
from ilias.constants import *
from ilias.login import login
from utils import *


async def producer(session, queue, fold_id, base_path=None):
    if base_path is None:
        base_path = "ilias"
    await search_tree(session, queue, fold_id, base_path)


async def search_tree(session, queue, fold_id, base_path):
    url = GOTO_URL + fold_id

    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)
    rows = soup.find_all("div", attrs={"class": "ilCLI ilObjListRow row"})
    for row in rows:
        content = row.find("div", attrs={"class": "ilContainerListItemContent"})
        link = content.find("a")
        href = link["href"]
        name = str(link.string)
        path = safe_path_join(base_path, name)
        if "download" in href:
            extension = str(content.find("span", attrs={"class": "il_ItemProperty"}).string).strip()
            await queue.put({"url": href, "path": f"{path}.{extension}"})
        else:
            ref_id = re.search("ref_id=([0-9]+)&", href).group(1)
            await search_tree(session, queue, ref_id, path)


if __name__ == "__main__":
    async def main():
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            await login(session)
            await producer(session, asyncio.Queue(), "187834")


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
