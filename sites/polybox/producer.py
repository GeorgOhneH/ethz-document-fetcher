import asyncio
import base64
import copy
import re
import os
import xml.etree.ElementTree as ET
from pathlib import PurePath
from urllib.parse import unquote, quote

import aiohttp

from core.constants import *
from core.downloader import download_if_not_exist
from core.monitor import MonitorSession
from sites.polybox.constants import *

logger = logging.getLogger(__name__)


async def login(session, poly_id, password):
    auth_url = INDEX_URL + f"{poly_id}/authenticate"

    async with session.get(auth_url) as response:
        auth_html = await response.text()

    match = re.search("""<input type="hidden" name="requesttoken" value="(.*)" />""", auth_html)
    requesttoken = match.group(1)

    data = {
        "requesttoken": requesttoken,
        "password": password,
    }
    async with session.post(auth_url, data=data) as response:
        await response.text()


async def authenticate(session, poly_id, password):
    poly_id_with_null = poly_id + ":null"

    headers = copy.copy(BASIC_HEADER)
    headers["Authorization"] = f"Basic {base64.b64encode(poly_id_with_null.encode('utf-8')).decode('utf-8')}"

    if password is not None:
        await login(session, poly_id, password)

    return headers


async def get_folder_name(session, id, password=None):
    poly_id = id
    async with MonitorSession(raise_for_status=True, signals=session.signals) as session:
        headers = await authenticate(session, poly_id, password)

        url = INDEX_URL + poly_id

        async with session.get(url=url, headers=headers) as response:
            html = await response.text()

        soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

        data_info = soup.body.header.div
        author = " ".join(data_info["data-owner-display-name"].split(" ")[:2])
        name = data_info["data-name"]
        return f"Polybox - {author}"


async def producer(session, queue, id, base_path, password=None):
    poly_id = id
    tasks = []
    # We create a new session, because polybox doesn't work
    # when you jump around with the same session
    async with MonitorSession(raise_for_status=True, signals=session.signals) as session:
        headers = await authenticate(session, poly_id, password)

        async with session.request("PROPFIND", url=WEBDAV_URL, data=PROPFIND_DATA, headers=headers) as response:
            xml = await response.text()

        tree = ET.fromstring(xml)

        for response in tree:
            href = go_down_tree(response, "d:href", to_text=True)
            prop = go_down_tree(response, "d:propstat", "d:prop")
            checksum = go_down_tree(prop, "oc:checksums", "oc:checksum", to_text=True)
            contenttype = go_down_tree(prop, "d:getcontenttype", to_text=True)
            if contenttype is None:
                continue

            path = PurePath(unquote(href))
            path = os.path.join(*path.parts[3:])
            absolute_path = os.path.join(base_path, path)
            files = os.path.basename(href)
            url_path = quote(os.path.join("/", os.path.dirname(path)).replace("\\", "/")).replace("/", "%2F")

            url = f"{INDEX_URL}{poly_id}/download?files={files}&path={url_path}"
            if password is not None:
                coroutine = download_if_not_exist(session, path=absolute_path, url=url,
                                                  checksum=checksum, **queue.consumer_kwargs)
                tasks.append(asyncio.ensure_future(coroutine))
            else:
                await queue.put({"url": url, "path": absolute_path, "checksum": checksum})

        await asyncio.gather(*tasks)


def go_down_tree(tree, *args, to_text=False):
    if tree is None:
        return None

    for key in args:
        key = key.replace("d:", "{DAV:}").replace("oc:", "{http://owncloud.org/ns}")
        tree = tree.find(key)
        if tree is None:
            return None

    if to_text:
        return tree.text
    return tree
