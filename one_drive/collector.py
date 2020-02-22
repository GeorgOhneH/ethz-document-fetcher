import os
from urllib.parse import parse_qs, urlparse


async def collector(session, queue, driver_url, base_path):
    parameters = parse_qs(urlparse(driver_url).query)
    authkey = parameters['authkey'][0]
    resid = parameters['resid'][0]
    driver_id = resid.split('!')[0]

    api_url = f"https://api.onedrive.com/v1.0/drives/{driver_id}/items/{resid}/children?authkey={authkey}"

    async with session.get(api_url) as response:
        item_data = await response.json()

    for item in item_data["value"]:
        path = os.path.join(base_path, item["name"])
        await queue.put({"path": path, "url": item["@content.downloadUrl"]})
