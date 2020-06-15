import asyncio
from urllib.parse import parse_qs, urlparse

import aiohttp

from core.storage import check_url_reference
from core.storage.utils import call_function_or_cache
from core.utils import *


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


async def producer(session, queue, base_path, url, etag=None):
    parameters = parse_qs(urlparse(url).query)
    api_url = get_api_url(parameters, children=True)
    authkey = parameters['authkey'][0]

    item_data = await call_function_or_cache(get_json_response, etag, session, api_url)

    tasks = []
    for item in item_data["value"]:
        path = safe_path_join(base_path, item["name"])
        if "@content.downloadUrl" in item:
            checksum = item["file"]["hashes"]["sha256Hash"]
            await queue.put({"path": path, "url": item["@content.downloadUrl"], "checksum": checksum})

        elif "folder" in item:
            folder_url = await check_url_reference(session, item['webUrl']) + f"?authkey={authkey}"
            item_etag = item["lastModifiedDateTime"]
            coroutine = producer(session, queue, path, f"{folder_url}?authkey={authkey}", etag=item_etag)
            tasks.append(asyncio.ensure_future(coroutine))

    await asyncio.gather(*tasks)


async def get_json_response(session, api_url):
    async with session.get(api_url) as response:
        return await response.json()


if __name__ == "__main__":
    async def main():
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            pass


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
