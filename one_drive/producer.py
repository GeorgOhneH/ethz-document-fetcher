import asyncio
from urllib.parse import parse_qs, urlparse

import aiohttp

from one_drive.constants import *
from utils import *


def get_api_url(parameters, children=True):
    authkey = parameters['authkey'][0]
    if "resid" in parameters:
        one_id = parameters['resid'][0]
    else:
        one_id = parameters['id'][0]
    driver_id = one_id.split('!')[0]

    child_string = "/children" if children else ""

    api_url = f"https://api.onedrive.com/v1.0/drives/{driver_id}/items/{one_id}{child_string}?authkey={authkey}"
    return api_url


async def get_folder_name(session, url):
    parameters = parse_qs(urlparse(url).query)
    api_url = get_api_url(parameters, children=False)

    async with session.get(api_url) as response:
        item_data = await response.json()

    return item_data["name"]


async def producer(session, queue, driver_url, base_path):
    parameters = parse_qs(urlparse(driver_url).query)
    api_url = get_api_url(parameters, children=True)
    authkey = parameters['authkey'][0]

    async with session.get(api_url) as response:
        item_data = await response.json()

    for item in item_data["value"]:
        path = safe_path_join(base_path, item["name"])
        if item.get("@content.downloadUrl", None) is not None:
            await queue.put({"path": path, "url": item["@content.downloadUrl"]})

        elif item.get("folder", None) is not None:
            url_reference_path = os.path.join(CACHE_PATH, "url.json")
            folder_url = await check_url_reference(session, item['webUrl'], url_reference_path)
            await producer(session, queue, f"{folder_url}?authkey={authkey}", path)


if __name__ == "__main__":
    async def main():
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            await producer(session, None,
                           "https://onedrive.live.com/?cid=b8180e91f886ea8a&id=B8180E91F886EA8A%21155601&authkey=!APFF5FVBjgYLHK8",
                           None)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
