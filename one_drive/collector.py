from urllib.parse import parse_qs, urlparse

from utils import *
from .constants import *


async def collector(session, queue, driver_url, base_path):
    parameters = parse_qs(urlparse(driver_url).query)
    authkey = parameters['authkey'][0]
    resid = parameters['resid'][0]
    driver_id = resid.split('!')[0]

    api_url = f"https://api.onedrive.com/v1.0/drives/{driver_id}/items/{resid}/children?authkey={authkey}"

    async with session.get(api_url) as response:
        item_data = await response.json()

    for item in item_data["value"]:
        path = os.path.join(base_path, item["name"].replace("/", " "))
        if item.get("@content.downloadUrl", None) is not None:
            await queue.put({"path": path, "url": item["@content.downloadUrl"]})

        elif item.get("folder", None) is not None:
            url_reference_path = os.path.join(CACHE_PATH, "url.json")
            folder_url = await check_url_reference(session, item['webUrl'], url_reference_path)
            await collector(session, queue, f"{folder_url}?authkey={authkey}", path)
