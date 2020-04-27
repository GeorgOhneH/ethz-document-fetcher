import asyncio
import importlib
import hashlib
import os
import json

import yaml

from utils import safe_path_join, debug_logger
from constants import CACHE_PATH

import logging

logger = logging.getLogger(__name__)

locks = {}


async def parse_folder(data, base_path, **kwargs):
    name = data["name"]
    path = os.path.join(base_path, name)
    await parse_producers(data=data["producers"], base_path=path, **kwargs)


async def parse_producers(data, **kwargs):
    tasks = []
    for producer_dict in data:
        producer_name, sub_data = list(producer_dict.items())[0]
        if producer_name == "folder":
            coroutine = parse_folder(data=sub_data, **kwargs)
        else:
            coroutine = parse_producer(producer_name=producer_name, p_kwargs=sub_data, **kwargs)
        tasks.append(asyncio.create_task(coroutine))

    await asyncio.gather(*tasks)


async def parse_producer(session, queue, producers, producer_name, p_kwargs, base_path, folder_name_cache):
    sub_producer = p_kwargs.pop("producers", None)
    folder = p_kwargs.pop("folder", None)
    folder_name = p_kwargs.pop("folder_name", None)
    use_folder = p_kwargs.pop("use_folder", True)

    if producer_name != "custom":
        module_name = producer_name
        folder_module_name = producer_name
        function_name = "producer"
        folder_function_name = "get_folder_name"
    else:
        module_name, function_name = get_module_function(p_kwargs.pop("function"))
        if folder_name is None and use_folder:
            folder_module_name, folder_function_name = get_module_function(p_kwargs.pop("folder_function"))
        else:
            folder_module_name, folder_function_name = None, None

    for key, value in p_kwargs.items():
        if value is None:
            raise ValueError(f"{key} is not allowed to be null")

    producer_module = importlib.import_module(module_name)
    producer_function = getattr(producer_module, function_name)
    await call_if_never_called(session, producer_module, "login")

    if use_folder:
        if folder_name is None:
            if folder_module_name == module_name:
                folder_module = producer_module
            else:
                folder_module = importlib.import_module(folder_module_name)
            folder_function = getattr(folder_module, folder_function_name)
            folder_name = await get_folder_name(session, folder_function, folder_name_cache, p_kwargs)

        base_path = safe_path_join(base_path, folder_name)

    coroutine = debug_logger(producer_function)(session=session, queue=queue, base_path=base_path, **p_kwargs)
    producers.append(asyncio.create_task(coroutine))

    if sub_producer is not None:
        await parse_producers(session=session, queue=queue, producers=producers, data=sub_producer,
                              base_path=base_path, folder_name_cache=folder_name_cache)
    if folder is not None:
        await parse_folder(session=session, queue=queue, producers=producers, data=folder,
                           base_path=base_path, folder_name_cache=folder_name_cache)


async def parse(session, queue, producers, path, base_path=""):
    with open(path) as f:
        data = yaml.load(f, Loader=yaml.Loader)

    md5 = hashlib.md5(str(data).encode('utf-8')).hexdigest()

    folder_name_cache = get_folder_name_cache(md5)

    tasks = []
    for key, value in data.items():
        if key == "folder":
            coroutine = parse_folder(session=session, queue=queue, producers=producers, data=value,
                                     base_path=base_path, folder_name_cache=folder_name_cache)
        elif key == "producers":
            coroutine = parse_producers(session=session, queue=queue, producers=producers, data=value,
                                        base_path=base_path, folder_name_cache=folder_name_cache)
        else:
            raise ValueError(f"Unexpected key, expected ('folder' or 'producers') not {key}")
        tasks.append(asyncio.create_task(coroutine))

    await asyncio.gather(*tasks)

    save_folder_name_cache(md5, folder_name_cache)


async def call_if_never_called(session, module, function_name):
    if not hasattr(module, function_name):
        return

    func = getattr(module, function_name)
    if not callable(func):
        return

    if module.__name__ in locks:
        lock = locks[module.__name__]
    else:
        lock = asyncio.Lock()
        locks[module.__name__] = lock

    async with lock:
        if not hasattr(func, "called"):
            func.called = True
            logger.debug(f"Logging into {module.__name__}")
            await func(session=session)


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


async def get_folder_name(session, function, folder_name_cache, p_kwargs):
    unique_string = function.__module__ + "." + function.__name__ + str(p_kwargs)
    if unique_string in folder_name_cache:
        return folder_name_cache[unique_string]
    logger.debug(f"Calling folder function: {unique_string}")
    folder_name = await function(session=session, **p_kwargs)
    folder_name_cache[unique_string] = folder_name
    return folder_name
