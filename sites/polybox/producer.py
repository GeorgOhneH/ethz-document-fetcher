import asyncio
import logging
import os
import re
import xml.etree.ElementTree as ET
from pathlib import PurePath
from urllib.parse import unquote

from aiohttp import BasicAuth
from bs4 import BeautifulSoup

from core.monitor import MonitorSession
from core.storage import cache
from core.utils import safe_path_join, get_beautiful_soup_parser, get_extension, add_extension
from settings.config_objs import ConfigOptions, ConfigString
from sites.exceptions import NotSingleFile
from sites.polybox.constants import *

logger = logging.getLogger(__name__)

POLY_TYPE_CONFIG = ConfigOptions(default="s",
                                 options=["s", "f"],
                                 optional=True,
                                 gui_name="Type",
                                 hint_text="Type s: Shared folder.<br>"
                                           "Type f: Private folder (your own polybox)")
POLY_ID_CONFIG = ConfigString(gui_name="ID")
PASSWORD_CONFIG = ConfigString(gui_name="Password", optional=True)


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
        pass


async def _get_dire_path(session, download_settings, poly_type, poly_id):
    url = INDEX_URL + poly_type + "/" + poly_id
    auth = BasicAuth(login=download_settings.username, password=download_settings.password)
    async with session.get(url=url, auth=auth) as response:
        dir_path = response.url.query["dir"]

    return dir_path


async def get_folder_name(session, download_settings, poly_id, poly_type="s", password=None):
    # We create a new session, because polybox doesn't work
    # when you jump around with the same session
    async with MonitorSession(raise_for_status=True, signals=session.signals) as session:
        if poly_type == "s":
            return await _get_folder_name_s(session=session,
                                            poly_type=poly_type,
                                            poly_id=poly_id,
                                            password=password)
        elif poly_type == "f":
            return await _get_folder_name_f(session=session,
                                            download_settings=download_settings,
                                            poly_type=poly_type,
                                            poly_id=poly_id)
        else:
            raise ValueError(f"poly_type value: {poly_type} not allowed")


async def _get_folder_name_s(session, poly_type, poly_id, password=None):
    if password is not None:
        await login_folder(session, poly_type, poly_id, password)

    url = INDEX_URL + poly_type + "/" + poly_id

    async with session.get(url=url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, get_beautiful_soup_parser())

    data_info = soup.body.header.div
    author = " ".join(data_info["data-owner-display-name"].split(" ")[:2])
    name = data_info["data-name"]
    return name


async def _get_folder_name_f(session, download_settings, poly_type, poly_id):
    dire_path = await _get_dire_path(session=session,
                                     download_settings=download_settings,
                                     poly_type=poly_type,
                                     poly_id=poly_id)
    folder_name = dire_path.split("/")[-1]

    if folder_name:
        return folder_name

    return "Polybox Root Folder"


async def producer(session,
                   queue,
                   base_path,
                   download_settings,
                   poly_id: POLY_ID_CONFIG,
                   poly_type: POLY_TYPE_CONFIG = "s",
                   password: PASSWORD_CONFIG = None):
    if poly_type == "f":
        await _producer_f(session=session,
                          queue=queue,
                          base_path=base_path,
                          download_settings=download_settings,
                          poly_type=poly_type,
                          poly_id=poly_id)
    elif poly_type == "s":
        await _producer_s(session=session,
                          queue=queue,
                          base_path=base_path,
                          poly_id=poly_id,
                          password=password)
    else:
        raise ValueError(f"poly_type value: {poly_type} not allowed")


async def _producer_s(session, queue, base_path, poly_id, password):
    auth = BasicAuth(login=poly_id,
                     password="null" if password is None else password)

    await _parse_tree(session=session,
                      queue=queue,
                      base_path=base_path,
                      url=WEBDAV_PUBLIC_URL,
                      auth=auth)


async def _producer_f(session, queue, base_path, download_settings, poly_type, poly_id):
    dir_path = await _get_dire_path(session=session,
                                    download_settings=download_settings,
                                    poly_type=poly_type,
                                    poly_id=poly_id)

    cut_parts_num = 5 + len([x for x in dir_path.split("/") if x.strip() != ""])

    url = f"{USER_WEBDAV_URL}{download_settings.username}{dir_path}"

    auth = BasicAuth(login=download_settings.username,
                     password=download_settings.password)

    await _parse_tree(session=session,
                      queue=queue,
                      base_path=base_path,
                      url=url,
                      auth=auth,
                      cut_parts_num=cut_parts_num)


async def _parse_tree(session, queue, base_path, url, auth, cut_parts_num=3):
    tasks = []

    async with session.request("PROPFIND", url=url, data=PROPFIND_DATA, headers=BASIC_HEADER, auth=auth) as response:
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
        path = safe_path_join("", *path.parts[cut_parts_num:])

        if not path:
            raise ValueError("Can not download single file")

        url = BASE_URL + href
        absolute_path = os.path.join(base_path, path)

        await queue.put({"url": url,
                         "path": absolute_path,
                         "checksum": checksum,
                         "session_kwargs": {"auth": auth},
                         })

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


async def parse_single_file(session,
                            queue,
                            base_path,
                            poly_id,
                            poly_type="s",
                            name=None,
                            password=None):
    if poly_type != "s":
        raise NotSingleFile()

    auth = BasicAuth(login=poly_id,
                     password="null" if password is None else password)

    async with session.request("PROPFIND", url=WEBDAV_PUBLIC_URL, data=PROPFIND_DATA, headers=BASIC_HEADER,
                               auth=auth) as response:
        xml = await response.text()

    tree = ET.fromstring(xml)
    if len(tree) != 1:
        raise NotSingleFile()

    response = tree[0]

    status = go_down_tree(response, "d:propstat", "d:status", to_text=True)

    if status != "HTTP/1.1 200 OK":
        return

    url = f"{INDEX_URL}s/{poly_id}/download"
    orig_filename = await cache.check_filename(session, url, session_kwargs={"auth": auth})

    if orig_filename is None:
        raise NotSingleFile()

    extension = get_extension(orig_filename)

    if name:
        filename = add_extension(name, extension)
    else:
        filename = orig_filename

    await queue.put({"url": url,
                     "path": safe_path_join(base_path, filename),
                     "session_kwargs": {"auth": auth},
                     })
