import asyncio
import importlib
import hashlib
import os
import json
import copy
import types
import inspect

import yaml

from exceptions import ParseModelError
from utils import safe_path_join, debug_logger
from constants import CACHE_PATH

import logging

logger = logging.getLogger(__name__)

locks = {}


def wrapper(obj, attr):
    def inside(*args, **kwargs):
        getattr(obj, attr)(*args, **kwargs)

    return inside


def wrapper_async(obj, attr, **consumer_kwargs):
    async def inside(*args, **kwargs):
        if attr == "put":
            if kwargs.get("item"):
                kwargs["item"].update(consumer_kwargs)
            else:
                args[0].update(consumer_kwargs)

        await getattr(obj, attr)(*args, **kwargs)

    return inside


class QueueWrapper:
    def __init__(self, obj, **kwargs):
        self.consumer_kwargs = kwargs
        for attr, method in obj.__class__.__dict__.items():
            if callable(method):
                if inspect.iscoroutinefunction(method):
                    setattr(self, attr, wrapper_async(obj, attr, **kwargs))
                else:
                    setattr(self, attr, wrapper(obj, attr))


async def parse_folder(data, base_path, **kwargs):
    if "name" not in data:
        raise ParseModelError("Expected a 'name' field in folder")

    name = data["name"]
    path = os.path.join(base_path, name)

    if "producers" not in data:
        raise ParseModelError("Expected a 'producers' field in folder")

    await parse_producers(data=data["producers"], base_path=path, **kwargs)


async def parse_producers(data, **kwargs):
    tasks = []
    for producer_dict in data:
        if len(producer_dict) > 1:
            raise ParseModelError(f"Expected a producer with only one key (not {len(producer_dict)})")

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
    possible_consumer_kwargs = ["allowed_extensions", "forbidden_extensions"]
    consumer_kwargs = {name: p_kwargs.pop(name, None) for name in possible_consumer_kwargs}
    consumer_kwargs = {name: value for name, value in consumer_kwargs.items() if value is not None}

    if producer_name != "custom":
        module_name = producer_name
        folder_module_name = producer_name
        function_name = "producer"
        folder_function_name = "get_folder_name"
    else:
        if "function" not in p_kwargs:
            raise ParseModelError(f"Expected a 'function' field with custom")
        module_name, function_name = get_module_function(p_kwargs.pop("function"))
        if folder_name is None and use_folder:
            if "function" not in p_kwargs:
                raise ParseModelError(f"Expected a 'folder_function' or 'folder_name' field with custom")
            folder_module_name, folder_function_name = get_module_function(p_kwargs.pop("folder_function"))
        else:
            folder_module_name, folder_function_name = None, None

    for key, value in p_kwargs.items():
        if value is None:
            raise ParseModelError(f"{key} is not allowed to be null")

    try:
        producer_module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        raise ParseModelError(f"Producer with name: {module_name} does not exist")

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

    queue_wrapper = QueueWrapper(queue, **consumer_kwargs)

    coroutine = debug_logger(producer_function)(session=session, queue=queue_wrapper, base_path=base_path, **p_kwargs)
    producers.append(asyncio.create_task(coroutine))

    if sub_producer is not None:
        await parse_producers(
            session=session,
            queue=queue,
            producers=producers,
            data=sub_producer,
            base_path=base_path,
            folder_name_cache=folder_name_cache
        )
    if folder is not None:
        await parse_folder(
            session=session,
            queue=queue,
            producers=producers,
            data=folder,
            base_path=base_path,
            folder_name_cache=folder_name_cache
        )


async def parse(session, queue, producers, path, base_path=""):
    with open(path) as f:
        data = yaml.load(f, Loader=yaml.Loader)

    md5 = hashlib.md5(str(data).encode('utf-8')).hexdigest()

    folder_name_cache = get_folder_name_cache(md5)
    tasks = []
    for key, value in data.items():
        if key == "folder":
            coroutine = parse_folder(
                session=session,
                queue=queue,
                producers=producers,
                data=value,
                base_path=base_path,
                folder_name_cache=folder_name_cache
            )
        elif key == "producers":
            coroutine = parse_producers(
                session=session,
                queue=queue,
                producers=producers,
                data=value,
                base_path=base_path,
                folder_name_cache=folder_name_cache
            )
        else:
            raise ParseModelError(f"Expected 'folder' or 'producers' field (not {key})")
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
            logger.debug(f"Logged into {module.__name__}")


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
