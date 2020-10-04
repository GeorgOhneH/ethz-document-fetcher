import asyncio
import base64
import copy
import logging
import os
import re
import xml.etree.ElementTree as ET
from pathlib import PurePath
from urllib.parse import unquote, quote, urlparse

from bs4 import BeautifulSoup

from core.constants import BEAUTIFUL_SOUP_PARSER
from core.downloader import download_if_not_exist
from core.monitor import MonitorSession
from core.utils import safe_path_join
from settings.config_objs import ConfigOptions
from sites.polybox.constants import *

logger = logging.getLogger(__name__)

poly_type_config = ConfigOptions(default="s", options=["s", "f"], optional=True)


async def login_folder(session, poly_type, poly_id, password, **kwargs):
    auth_url = INDEX_URL + f"{poly_type}/{poly_id}/authenticate"

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


async def login_user(session, site_settings):
    async with session.get(LOGIN_USER_URL) as response:
        auth_html = await response.text()

    match = re.search("""<input type="hidden" name="requesttoken" value="(.*)">""", auth_html)
    requesttoken = match.group(1)
    data = {
        "user": site_settings.username,
        "password": site_settings.password,
        "timezone-offset": "2",
        "timezone": "Europe/Berlin",
        "requesttoken": requesttoken,
    }
    async with session.post(LOGIN_USER_URL, data=data) as response:
        pass

    return {"requesttoken": requesttoken}


async def authenticate(session, site_settings, poly_type, poly_id, password):
    if poly_type == "f":
        headers = copy.copy(BASIC_HEADER)
        headers.update(await login_user(session, site_settings))

        url = INDEX_URL + poly_type + "/" + poly_id

        async with session.get(url=url) as response:
            dir_path = response.url.query["dir"]

        return f"{USER_WEBDAV_URL}{site_settings.username}{dir_path}", headers

    else:
        poly_id_with_null = poly_id + ":null"

        headers = copy.copy(BASIC_HEADER)
        headers["Authorization"] = f"Basic {base64.b64encode(poly_id_with_null.encode('utf-8')).decode('utf-8')}"

        if password is not None:
            await login_folder(session, poly_type, poly_id, password)

        return WEBDAV_PUBLIC_URL, headers


async def get_folder_name(session, site_settings, id, poly_type="s", password=None):
    poly_id = id
    async with MonitorSession(raise_for_status=True, signals=session.signals) as session:
        await authenticate(session=session,
                           site_settings=site_settings,
                           poly_type=poly_type,
                           poly_id=poly_id,
                           password=password)

        url = INDEX_URL + poly_type + "/" + poly_id

        async with session.get(url=url) as response:
            html = await response.text()
            if poly_type == "f":
                return _url_to_name(response.url)

        soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

        data_info = soup.body.header.div
        author = " ".join(data_info["data-owner-display-name"].split(" ")[:2])
        name = data_info["data-name"]
        return f"Polybox - {author}"


async def producer(session, queue, base_path, site_settings, id, poly_type: poly_type_config = "s", password=None):
    poly_id = id
    tasks = []
    # We create a new session, because polybox doesn't work
    # when you jump around with the same session
    async with MonitorSession(raise_for_status=True, signals=session.signals) as session:
        url, headers = await authenticate(session=session,
                                          site_settings=site_settings,
                                          poly_type=poly_type,
                                          poly_id=poly_id,
                                          password=password)

        async with session.request("PROPFIND", url=url, data=PROPFIND_DATA, headers=headers) as response:
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
            path = safe_path_join("", *path.parts[3:])

            if not path:
                raise ValueError("Can not download single file")

            files = os.path.basename(href)

            if poly_type == "f":
                url = WEBDAV_REMOTE_URL + path.replace("\\", "/").replace(f"files/{site_settings.username}/", "")
                absolute_path = os.path.join(base_path,  "\\".join(path.split("\\")[4:]))
            else:
                url_path = quote(os.path.join("/", os.path.dirname(path)).replace("\\", "/")).replace("/", "%2F")
                url = f"{INDEX_URL}{poly_type}/{poly_id}/download?files={files}&path={url_path}"
                absolute_path = os.path.join(base_path, path)

            if password is not None or poly_type == "f":
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


def _url_to_name(url):
    return url.query["dir"].split("/")[-1]
