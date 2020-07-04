import copy
import json
import logging
import os
import pickle
import random

from core.storage import cache
from core.storage.constants import FUNCTION_CACHE_PATH

logger = logging.getLogger(__name__)


def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False


async def call_function_or_cache(func, identifier, *args, **kwargs):
    json_name = func.__module__ + "." + func.__name__
    table = cache.get_json(json_name)

    func_identifier = get_func_identifier(args, kwargs)
    attributes = table.get(func_identifier, {})
    cache_identifier = copy.copy(attributes.get("identifier", None))
    try:
        if identifier is not None and identifier == cache_identifier:
            if attributes["pickle"]:
                with open(attributes["value"], "rb") as f:
                    return pickle.load(f)

            return attributes["value"]
    except FileNotFoundError:
        logger.warning("Pickle file could not be found")
        pass

    result = await func(*args, **kwargs)

    if identifier is not None:
        logger.debug(f"Called function: {json_name}, func_identifier: {func_identifier}")
    attributes["identifier"] = identifier

    if is_jsonable(result):
        attributes["value"] = result
        attributes["pickle"] = False
    else:
        file_name = str(random.randint(1e18, 1e19)) + ".pickle"
        path = os.path.join(FUNCTION_CACHE_PATH, file_name)
        attributes["value"] = path
        attributes["pickle"] = True

        with open(path, "wb+") as f:
            pickle.dump(result, f)

    table[func_identifier] = attributes
    return result


def get_func_identifier(args, kwargs):
    result = ""
    for item in args:
        result += item_to_string(item)
    for key, item in kwargs.items():
        result += str(key) + ":" + item_to_string(item)

    return result


def item_to_string(item):
    if isinstance(item, (str, int)):
        return str(item)
    return ""
