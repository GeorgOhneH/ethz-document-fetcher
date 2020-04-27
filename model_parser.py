import asyncio
import importlib
import hashlib
import os
import json

import yaml

from utils import safe_path_join
from constants import CACHE_PATH

import logging

logger = logging.getLogger(__name__)


async def parse_folder(session, producers, data, base_path, folder_name_cache):
    name = data["name"]
    await parse_producers(session, producers, data["producers"], os.path.join(base_path, name), folder_name_cache)


async def parse_producers(session, producers, producer_dicts, base_path, folder_name_cache):
    tasks = []
    for producer_dict in producer_dicts:
        producer_name, kwargs = list(producer_dict.items())[0]
        if producer_name == "folder":
            coroutine = parse_folder(session, producers, kwargs, base_path, folder_name_cache)
        else:
            coroutine = parse_producer(session, producers, producer_name, kwargs, base_path, folder_name_cache)
        tasks.append(asyncio.create_task(coroutine))

    await asyncio.gather(*tasks)


async def parse_producer(session, producers, producer_name, kwargs, base_path, folder_name_cache):
    sub_producer = kwargs.pop("producers", None)
    folder = kwargs.pop("folder", None)
    folder_name = kwargs.pop("folder_name", None)
    use_folder = kwargs.pop("use_folder", True)

    if producer_name != "custom":
        module_name = producer_name
        folder_module_name = producer_name
        function_name = "producer"
        folder_function_name = "get_folder_name"
    else:
        module_name, function_name = get_module_function(kwargs.pop("function"))
        if folder_name is None and use_folder:
            folder_module_name, folder_function_name = get_module_function(kwargs.pop("folder_function"))
        else:
            folder_module_name, folder_function_name = None, None

    producer_module = importlib.import_module(module_name)
    producer_function = getattr(producer_module, function_name)

    if use_folder:
        if folder_name is None:
            folder_module = importlib.import_module(folder_module_name)
            folder_function = getattr(folder_module, folder_function_name)
            try:
                folder_name = await get_folder_name(session, folder_function, folder_name_cache, kwargs)
            except TypeError:
                raise ValueError(f"{folder_function_name}, {folder_module_name}")

        base_path = safe_path_join(base_path, folder_name)

    producers.append((producer_function, kwargs, base_path))

    if sub_producer is not None:
        await parse_producers(session, producers, sub_producer, base_path, folder_name_cache)
    if folder is not None:
        await parse_folder(session, producers, folder, base_path, folder_name_cache)


async def parse(session, producers, path, base_path=""):
    with open(path) as f:
        data = yaml.load(f, Loader=yaml.Loader)

    md5 = hashlib.md5(str(data).encode('utf-8')).hexdigest()

    folder_name_cache = get_folder_name_cache(md5)

    tasks = []
    for key, value in data.items():
        if key == "folder":
            coroutine = parse_folder(session, producers, value, base_path, folder_name_cache)
        elif key == "producers":
            coroutine = parse_producers(session, producers, value, base_path, folder_name_cache)
        else:
            raise ValueError(f"Unexpected key, expected ('folder' or 'producers') not {key}")
        tasks.append(asyncio.create_task(coroutine))

    await asyncio.gather(*tasks)

    save_folder_name_cache(md5, folder_name_cache)


def get_module_function(name):
    mf_name = ("custom." + name).split(".")
    module_name = ".".join(mf_name[:-1])
    function_name = mf_name[-1]
    return module_name, function_name


def get_folder_name_cache(md5):
    path = os.path.join(CACHE_PATH, "folder_name.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        folder_name_cache = json.load(f)

    if md5 not in folder_name_cache:
        return {}

    logger.debug(f"Loading cache")
    return folder_name_cache[md5]


def save_folder_name_cache(md5, folder_name_cache):
    logger.debug("Saving cache")
    path = os.path.join(CACHE_PATH, "folder_name.json")
    with open(path, "w+") as f:
        json.dump({md5: folder_name_cache}, f)


async def get_folder_name(session, function, folder_name_cache, kwargs):
    unique_string = function.__module__ + function.__name__ + str(kwargs)
    if unique_string in folder_name_cache:
        return folder_name_cache[unique_string]
    logger.debug(f"Calling folder function: {unique_string}")
    folder_name = await function(session=session, **kwargs)
    folder_name_cache[unique_string] = folder_name
    return folder_name
