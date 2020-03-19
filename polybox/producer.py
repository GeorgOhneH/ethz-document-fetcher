import xml.etree.ElementTree as ET
import base64
from polybox.constants import *
import asyncio
import aiohttp
import copy
import os
from urllib.parse import unquote, quote
from pathlib import PurePath
import re
import time


async def producer(queue, poly_id, base_path=None, password=None):
    # We create a new session, because the polybox doesn't like it when you jump between different ones
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        poly_id_with_null = poly_id + ":null"

        headers = copy.copy(BASIC_HEADER)
        headers["Authorization"] = f"Basic {base64.b64encode(poly_id_with_null.encode('utf-8')).decode('utf-8')}"

        if password is not None:
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

            headers["requesttoken"] = requesttoken

        if base_path is None:
            base_path = f"polybox {poly_id}"

        async with session.request("PROPFIND", url=WEBDAV_URL, data=PROPFIND_DATA, headers=headers, raise_for_status=True) as response:
            xml = await response.text()

    tree = ET.fromstring(xml)

    for response in tree:
        href = go_down_tree(response, "d:href", to_text=True)
        prop = go_down_tree(response, "d:propstat", "d:prop")
        checksum = go_down_tree(prop, "oc:checksums", "oc:checksum", to_text=True)
        contenttype = go_down_tree(prop, "d:getcontenttype", to_text=True)
        if contenttype is not None:
            path = PurePath(unquote(href))
            path = os.path.join(*path.parts[3:])
            absolute_path = os.path.join(base_path, path)
            files = os.path.basename(href)
            url_path = quote(os.path.join("/", os.path.dirname(path)).replace("\\", "/")).replace("/", "%2F")

            url = f"{INDEX_URL}{poly_id}/download?files={files}&path={url_path}"
            await queue.put({"url": url, "path": absolute_path})


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


if __name__ == "__main__":
    async def main():
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            await producer(asyncio.Queue(), "SU2lkCtdoLH3X1w", password="NUS2020")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
