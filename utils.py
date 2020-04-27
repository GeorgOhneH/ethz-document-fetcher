import hashlib
import json
import os
from pathlib import Path
import time

import logging
logger = logging.getLogger(__name__)


async def user_statistics(session, name):
    if not name:
        return
    data = {
        'name': hashlib.md5(name.encode('utf-8')).hexdigest(),
    }
    async with session.post("https://ethz-document-fetcher.mikrounix.com/add", data=data) as response:
        pass


def debug_logger(function):
    async def wrapper(session, queue, base_path, *args,  **kwargs):
        function_name = f"{function.__module__}.{function.__name__} {kwargs}"
        logger.debug(f"Starting: {function_name}")
        t = time.time()
        result = await function(session=session, queue=queue, base_path=base_path, *args, **kwargs)
        logger.debug(f"Finished: {function_name}, time: {(time.time() - t):.2f}")
        return result

    return wrapper


async def check_url_reference(session, url, url_reference_path):
    url_reference = load_url_reference(url_reference_path)
    new_url = url_reference.get(url, None)

    if new_url is None:
        async with session.get(url, raise_for_status=False) as response:
            new_url = str(response.url)
        url_reference[url] = new_url
        save_url_reference(url_reference, url_reference_path)

    return new_url


def save_txt(section, path):
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "w+") as f:
        f.write(str(section))


def load_txt(path):
    with open(path, "r") as f:
        return f.read()


def load_url_reference(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_url_reference(url_reference, path):
    with open(path, "w+") as f:
        return json.dump(url_reference, f)


def safe_path_join(path, *paths):
    return os.path.join(path, *[safe_path(x) for x in paths if x])


def safe_path(string):
    return string.replace("/", "-")
