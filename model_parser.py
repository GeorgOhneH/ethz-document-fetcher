import asyncio
import importlib
import os

import yaml

from utils import safe_path_join


async def parse_folder(session, producers, data, base_path):
    name = data["name"]
    await parse_producers(session, producers, data["producers"], os.path.join(base_path, name))


async def parse_producers(session, producers, producer_dicts, base_path):
    tasks = []
    for producer_dict in producer_dicts:
        producer_name, kwargs = list(producer_dict.items())[0]
        if producer_name == "folder":
            tasks.append(asyncio.create_task(parse_folder(session, producers, data=kwargs, base_path=base_path)))
        else:
            tasks.append(asyncio.create_task(parse_producer(session, producers, producer_name, kwargs, base_path)))

    await asyncio.gather(*tasks)


async def parse_producer(session, producers, producer_name, kwargs, base_path):
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
                folder_name = await get_folder_name(session, folder_function, kwargs)
            except TypeError:
                raise ValueError(f"{folder_function_name}, {folder_module_name}")

        base_path = safe_path_join(base_path, folder_name)

    producers.append((producer_function, kwargs, base_path))

    if sub_producer is not None:
        await parse_producers(session, producers, sub_producer, base_path)
    if folder is not None:
        await parse_folder(session, producers, folder, base_path)


async def parse(session, producers, path, base_path=""):
    with open(path) as f:
        data = yaml.load(f, Loader=yaml.Loader)

    tasks = []
    for key, value in data.items():
        if key == "folder":
            tasks.append(asyncio.create_task(parse_folder(session, producers, value, base_path)))
        elif key == "producers":
            tasks.append(asyncio.create_task(parse_producers(session, producers, value, base_path)))

    await asyncio.gather(*tasks)


def get_module_function(name):
    mf_name = ("custom." + name).split(".")
    module_name = ".".join(mf_name[:-1])
    function_name = mf_name[-1]
    return module_name, function_name


async def get_folder_name(session, function, kwargs):
    return await function(session=session, **kwargs)
