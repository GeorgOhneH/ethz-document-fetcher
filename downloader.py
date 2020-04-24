import glob
import os
import re
import copy
import shutil
from pathlib import Path

import aiohttp
from colorama import Fore, Back, Style

from settings import settings

import logging
logger = logging.getLogger(__name__)


async def download_files(session: aiohttp.ClientSession, queue):
    while True:
        item = await queue.get()
        kwargs = item.get("kwargs", {})
        file_path = item.get("path")
        url = item.get("url")
        extension = item.get("extension", True)

        await download_if_not_exist(session, file_path, url, extension, kwargs)

        queue.task_done()


async def download_if_not_exist(session, file_path, url, extension=True, kwargs=None):
    if kwargs is None:
        kwargs = {}

    timeout = aiohttp.ClientTimeout(total=0)
    if os.path.isabs(file_path):
        absolute_path = file_path
    else:
        absolute_path = os.path.join(settings.base_path, file_path)

    drive, path = os.path.splitdrive(absolute_path)
    absolute_path = os.path.join(drive, path.replace(":", ";").replace("|", ""))

    Path(os.path.dirname(absolute_path)).mkdir(parents=True, exist_ok=True)

    if file_exists(absolute_path, extension):
        return

    file_name = os.path.basename(absolute_path)
    if extension:
        file_extension = get_extension(file_name)
        if file_extension.lower() in ["mp4", "webm", "avi", "mkv", "mov", "m4v"]:
            if not settings.download_videos:
                return
            logger.info(f"Starting to download {file_name}")

    async with session.get(url, timeout=timeout, **kwargs) as response:
        response.raise_for_status()

        if not extension:
            disposition = response.headers['content-disposition']
            resp_file_name = re.findall("""filename="(.+)"$""", disposition)[0]
            absolute_path += "." + get_extension(resp_file_name)
            file_name = os.path.basename(absolute_path)

        with open(absolute_path, 'wb') as f:
            while True:
                chunk = await response.content.read(256)
                if not chunk:
                    break
                f.write(chunk)

    start = {
        "name": f"Added new file: '{Fore.GREEN}{{}}{Style.RESET_ALL}'",
        "var": copy.copy(file_name),
        "priority": 100,
        "cut": "back",
    }

    end = {
        "name": " in '{}'",
        "var": copy.copy(os.path.dirname(absolute_path)),
        "priority": -100,
        "cut": "front",
    }

    logger.info(fit_sections_to_console(start, end, margin=-8))


def fit_sections_to_console(*args, filler="..", min_length=10, margin=0):
    min_length = len(filler) + min_length
    c, _ = shutil.get_terminal_size(fallback=(0, 0))
    orig_sections = list(args)
    sections = copy.copy(orig_sections)
    sections.sort(key=lambda s: -s["priority"])

    free = c - sum([len(x["name"])-2 for x in sections]) - margin - 6
    length_vars = []
    count = 0
    for section in reversed(sections):
        length_vars.append(count)
        count += min(len(section["var"]), min_length)
    length_vars.reverse()
    if c:
        for length_var, section in zip(length_vars, sections):
            c_free = free - length_var
            if c_free < len(section["var"]) and len(section["var"]) > min_length:
                cut_length = max(c_free, min_length)
                if section["cut"] == "front":
                    section["var"] = (filler + section["var"][-cut_length+len(filler):])
                elif section["cut"] == "back":
                    section["var"] = (section["var"][:cut_length-len(filler)] + filler)

            free -= len(section["var"])

    return "".join([x["name"].format(x["var"]) for x in orig_sections])


def get_extension(file):
    return file.split(".")[-1]


def file_exists(path, extension):
    if not extension:
        valid_paths = glob.glob(f"{path}.*")
        if len(valid_paths) > 2:
            logger.warning("Found file with same filename, but different extension, could cause problems")

        return len(valid_paths) >= 1

    return os.path.exists(path)
