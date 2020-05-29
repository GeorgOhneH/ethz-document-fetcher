import asyncio
import hashlib
import importlib
import inspect
import logging
import os
import re
import time
import traceback

import yaml

from core.exceptions import ParseTemplateError, LoginError
from core.storage import cache
from core.utils import safe_path_join
from settings import settings

logger = logging.getLogger(__name__)

locks = {}


def queue_wrapper(obj, attr):
    def inside(*args, **kwargs):
        getattr(obj, attr)(*args, **kwargs)

    return inside


def queue_wrapper_async(obj, attr, **consumer_kwargs):
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
                    setattr(self, attr, queue_wrapper_async(obj, attr, **kwargs))
                else:
                    setattr(self, attr, queue_wrapper(obj, attr))


async def parse_folder(data, base_path, **kwargs):
    if "name" not in data:
        raise ParseTemplateError("Expected a 'name' field in folder")

    name = data["name"]
    path = os.path.join(base_path, name)

    if "producers" not in data:
        raise ParseTemplateError("Expected a 'producers' field in folder")

    await parse_producers(data=data["producers"], base_path=path, **kwargs)


async def parse_producers(data, **kwargs):
    tasks = []
    for producer_dict in data:
        if len(producer_dict) > 1:
            raise ParseTemplateError(f"Expected a producer with only one key (not {len(producer_dict)})")

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

    if check_if_null(p_kwargs):
        logger.warning(f"Found a null field in {producer_name}. Skipping the producer and all sub-producers")
        return

    if producer_name != "custom":
        module_name = producer_name
        folder_module_name = producer_name
        function_name = "producer"
        folder_function_name = "get_folder_name"
    else:
        if "function" not in p_kwargs:
            raise ParseTemplateError(f"Expected a 'function' field with custom")
        module_name, function_name = get_module_function(p_kwargs.pop("function"))
        if folder_name is None and use_folder:
            if "function" not in p_kwargs:
                raise ParseTemplateError(f"Expected a 'folder_function' or 'folder_name' field with custom")
            folder_module_name, folder_function_name = get_module_function(p_kwargs.pop("folder_function"))
        else:
            folder_module_name, folder_function_name = None, None

    try:
        producer_module = importlib.import_module(module_name)

        producer_function = getattr(producer_module, function_name)

        await call_if_never_called(session, producer_module, "login")

    except asyncio.CancelledError as e:
        raise asyncio.CancelledError() from e

    except ModuleNotFoundError:
        raise ParseTemplateError(f"Producer module with name: {module_name} does not exist")

    except AttributeError:
        raise ParseTemplateError(f"Function: {function_name} in module: {module_name} does not exist")

    except LoginError as e:
        if settings.loglevel == "DEBUG":
            traceback.print_exc()
        logger.warning(f"{module_name} login was not successful. Error: {e}."
                       f" Skipping the producer and all sub-producers")
        return

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

    coroutine = exception_handler(producer_function)(session=session, queue=queue_wrapper,
                                                     base_path=base_path, **p_kwargs)

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


def check_if_null(p_kwargs):
    for key, value in p_kwargs.items():
        if value is None:
            return True
    return False


async def parse_template(session, queue, producers, path, base_path=""):
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
            raise ParseTemplateError(f"Expected 'folder' or 'producers' field (not {key})")
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
        if not hasattr(func, "error"):
            logger.debug(f"Logging into {module.__name__}")
            start_time = time.time()
            try:
                await func(session=session)
                logger.debug(f"Logged into {module.__name__}, time: {(time.time()-start_time):.2f}")
                func.error = False
            except LoginError as e:
                func.error = True
                raise e
        if func.error:
            raise LoginError("Previous login was not successful")


def get_module_function(name):
    mf_name = ("custom." + name).split(".")
    module_name = ".".join(mf_name[:-1])
    function_name = mf_name[-1]
    return module_name, function_name


def get_folder_name_cache(md5):
    folder_name_cache = cache.get_json("folder_name")

    if md5 not in folder_name_cache:
        return {}

    return folder_name_cache[md5]


def save_folder_name_cache(md5, folder_name_cache):
    cache.set_json("folder_name", {md5: folder_name_cache})


async def get_folder_name(session, function, folder_name_cache, p_kwargs):
    unique_string = function.__module__ + "." + function.__name__ + f"<{dict_to_string(p_kwargs)}>"
    if unique_string in folder_name_cache:
        return folder_name_cache[unique_string]
    logger.debug(f"Calling folder function: {unique_string}")
    folder_name = await exception_handler_folder_name(function)(session=session, **p_kwargs)
    folder_name_cache[unique_string] = folder_name
    return folder_name


def exception_handler(function):
    async def wrapper(session, queue, base_path, *args, **kwargs):
        function_name = f"{function.__module__}.{function.__name__}"
        function_name_kwargs = f"{function_name}<{dict_to_string(kwargs)}>"
        try:
            logger.debug(f"Starting: {function_name_kwargs}")
            t = time.time()
            result = await function(session=session, queue=queue, base_path=base_path, *args, **kwargs)
            logger.debug(f"Finished: {function_name_kwargs}, time: {(time.time() - t):.2f}")
            return result
        except asyncio.CancelledError:
            raise asyncio.CancelledError()
        except TypeError as e:
            if settings.loglevel == "DEBUG":
                traceback.print_exc()
            keyword = re.findall("'(.+)'", e.args[0])
            logger.error(f"The producer {function_name_kwargs} got an unexpected keyword: {keyword}."
                         f" Stopping the producer..")
            return None
        except Exception as e:
            if settings.loglevel == "DEBUG":
                traceback.print_exc()
            logger.error(f"Got an unexpected error from producer: {function_name_kwargs}, "
                         f"Error: {type(e).__name__}: {e}")

    return wrapper


def exception_handler_folder_name(function):
    async def wrapper(session, *args, **kwargs):
        function_name = f"{function.__module__}.{function.__name__}"
        function_name_kwargs = f"{function_name}<{dict_to_string(kwargs)}>"
        try:
            return await function(session=session, *args, **kwargs)
        except asyncio.CancelledError:
            raise asyncio.CancelledError()
        except TypeError as e:
            if settings.loglevel == "DEBUG":
                traceback.print_exc()
            keyword = re.findall("'(.+)'", e.args[0])
            logger.error(f"The producer got an unexpected keyword: {keyword}")
            raise ParseTemplateError() from e
        except Exception as e:
            if settings.loglevel == "DEBUG":
                traceback.print_exc()
            logger.error(f"Got an unexpected error from get_folder_name: {function_name_kwargs}, "
                         f"Error: {type(e).__name__}: {e}")
            raise ParseTemplateError() from e

    return wrapper


def dict_to_string(d):
    result = ""
    for key, value in d.items():
        result += str(key) + "=" + str(value) + " "
    if d:
        result = result[:-1]
    return result
