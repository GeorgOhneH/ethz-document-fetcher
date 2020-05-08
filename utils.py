import hashlib
import json
import html
import os
from pathlib import Path
import time
import atexit
import re

import logging

from constants import CACHE_PATH

logger = logging.getLogger(__name__)


async def user_statistics(session, name):
    if not name:
        return
    data = {
        'name': hashlib.md5(name.encode('utf-8')).hexdigest(),
    }
    async with session.post("https://ethz-document-fetcher.mikrounix.com/add", data=data) as response:
        pass


def load_lockup_table(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_lockup_table(path):
    with open(path, "w+") as f:
        return json.dump(lockup_table, f)


def clean_lockup_table():
    logger.debug("Cleaning up lockup table")
    path = os.path.join(CACHE_PATH, "lockup_table.json")
    save_lockup_table(path)


lockup_table = load_lockup_table(os.path.join(CACHE_PATH, "lockup_table.json"))
atexit.register(clean_lockup_table)


async def check_url_reference(session, url):
    new_url = lockup_table.get(url, None)

    if new_url is None:
        async with session.get(url, raise_for_status=False) as response:
            new_url = str(response.url)
        lockup_table[url] = new_url
        logger.debug(f"Called url_reference, url: {url}, new url: {new_url}")

    return new_url


async def check_extension_cache(session, path, url):
    extension = lockup_table.get(path+url, None)

    if extension is None:
        async with session.get(url, raise_for_status=True) as response:
            extension = get_extension_from_response(response)
        lockup_table[path+url] = extension
        logger.debug(f"Called extension_cache, path+url: {path+url}, new url: {extension}")

    return path + "." + extension


def is_checksum_same(key, checksum):
    if checksum is None:
        return True

    old_checksum = lockup_table.get(key, None)

    if old_checksum is None:
        lockup_table[key] = checksum
        logger.debug(f"Added new checksum, key: {key}, checksum: {checksum}")
        return False

    if old_checksum == checksum:
        return True

    lockup_table[key] = checksum
    logger.debug(f"Replaced old checksum, key: {key}, new checksum: {checksum}, old checksum {old_checksum}")
    return False


def get_extension_from_response(response):
    disposition = response.headers['content-disposition']
    resp_file_name = re.search("""filename="(.+).""", disposition)[1]
    return get_extension(resp_file_name)


def get_extension(file):
    return file.split(".")[-1]


def save_txt(section, path):
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "w+") as f:
        f.write(str(section))


def load_txt(path):
    with open(path, "r") as f:
        return f.read()


def safe_path_join(path, *paths):
    return os.path.join(path, *[safe_path(x) for x in paths if x])


def safe_path(string):
    return html.unescape(string.replace("/", "-"))


async def check_for_new_release(session):
    path = os.path.join(os.path.dirname(__file__), "version.txt")
    with open(path) as f:
        current_version = f.readline().strip()

    async with session.get("https://api.github.com/repos/GeorgOhneH/ethz-document-fetcher/releases/latest") as response:
        data = await response.json()

    latest_version = data["tag_name"]
    c_v_i = [int(x) for x in current_version[1:].split(".")]
    l_v_i = [int(x) for x in latest_version[1:].split(".")]
    for i, latest_i in enumerate(l_v_i):
        current_i = c_v_i[i] if i < len(c_v_i) else 0
        if latest_i > current_i:
            return True, latest_version, current_version
        elif latest_i < current_i:
            return False, latest_version, current_version
    return False, latest_version, current_version

