import json
import logging
import os

from core.storage.utils import get_json_cache_path
from core.utils import get_extension_from_response, get_filename_from_response

logger = logging.getLogger(__name__)

loaded_jsons = {}


def get_json(name):
    if name not in loaded_jsons:
        load_json(name)
    return loaded_jsons[name]["value"]


def set_json(name, value, path):
    item = {
        "value": value,
        "meta": {
            "path": path,
        },
    }
    loaded_jsons[name] = item


def load_json(name):
    logger.debug(f"Loading {name} json")
    path = os.path.join(get_json_cache_path(), name + ".json")
    if not os.path.exists(path):
        set_json(name, {}, path)
    else:
        with open(path, "r") as f:
            set_json(name, json.load(f), path)


def save_json(path, value):
    with open(path, "w+") as f:
        json.dump(value, f)


def save_jsons():
    logger.debug("Cleaning up lockup table")
    for name, item in loaded_jsons.items():
        path = item["meta"]["path"]
        save_json(path, item["value"])
    loaded_jsons.clear()


def get_file_meta_data(path):
    table = get_json("file_meta_data")
    if path not in table:
        table[path] = {}
    return table[path]


async def check_url_reference(session, url):
    table = get_json("url_reference")
    new_url = table.get(url, None)

    if new_url is None:
        async with session.get(url, raise_for_status=False) as response:
            new_url = str(response.url)
        table[url] = new_url
        logger.debug(f"Called url_reference, url: {url}, new url: {new_url}")

    return new_url


async def check_extension(session, url, session_kwargs=None):
    if session_kwargs is None:
        session_kwargs = {}

    table = get_json("extensions")
    if url in table:
        return table[url]

    async with session.get(url, raise_for_status=True, **session_kwargs) as response:
        extension = get_extension_from_response(response)

    table[url] = extension
    logger.debug(f"Called filename_cache, url: {url}, extension: {extension}")

    return extension


async def check_filename(session, url, session_kwargs=None):
    if session_kwargs is None:
        session_kwargs = {}

    table = get_json("filenames")
    if url in table:
        return table[url]

    async with session.get(url, raise_for_status=True, **session_kwargs) as response:
        filename = get_filename_from_response(response)

    table[url] = filename
    logger.debug(f"Called filename_cache, url: {url}, extension: {filename}")

    return filename


def is_checksum_same(path, checksum):
    if checksum is None:
        return True

    meta_data = get_file_meta_data(path)

    old_checksum = meta_data.get("checksum", None)

    if old_checksum is None:
        return False

    if old_checksum == checksum:
        return True

    return False


def is_own_checksum_same(path, checksum):
    if not isinstance(checksum, str):
        raise ValueError(f"own_checksum must be a string. Not {type(checksum)}")

    meta_data = get_file_meta_data(path)

    old_checksum = meta_data.get("own_checksum", None)

    if old_checksum is None:
        return False

    if old_checksum == checksum:
        return True

    return False


def save_checksum(path, checksum):
    if checksum is None:
        return

    meta_data = get_file_meta_data(path)

    old_checksum = meta_data.get("checksum", None)

    if old_checksum == checksum:
        return

    if old_checksum is None:
        logger.debug(f"Added new checksum, path: {path}, checksum: {checksum}")
    else:
        logger.debug(f"Replaced old checksum, path: {path}, new: {checksum}, old: {old_checksum}")

    meta_data["checksum"] = checksum


def save_own_checksum(path, checksum):
    if not isinstance(checksum, str):
        raise ValueError(f"checksum must be a string. Not {type(checksum)}")

    meta_data = get_file_meta_data(path)

    old_checksum = meta_data.get("own_checksum", None)

    if old_checksum == checksum:
        return

    if old_checksum is None:
        logger.debug(f"Added new own_checksum, path: {path}, checksum: {checksum}")
    else:
        logger.debug(f"Replaced old own_checksum, path: {path}, new: {checksum}, old: {old_checksum}")

    meta_data["own_checksum"] = checksum


def get_etag(path):
    meta_data = get_file_meta_data(path)
    return meta_data.get("etag", None)


def save_etag(path, etag):
    etag = etag.replace("-gzip", "")
    meta_data = get_file_meta_data(path)
    if "etag" in meta_data:
        logger.debug(f"Replacing etag. Old: {meta_data['etag']}, New: {etag}")
    else:
        logger.debug(f"Adding new etag. New: {etag}")

    meta_data["etag"] = etag
