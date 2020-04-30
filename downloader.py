import copy
import glob
import logging
import os
import re
import shutil
import traceback
import asyncio
import sys
from pathlib import Path

import aiohttp
from colorama import Fore, Style
from constants import *

from settings import settings

logger = logging.getLogger(__name__)


async def download_files(session: aiohttp.ClientSession, queue):
    while True:
        item = await queue.get()
        try:
            await download_if_not_exist(session, **item)
        except asyncio.CancelledError:
            return
        except Exception as e:
            if settings.loglevel == "DEBUG":
                traceback.print_exc()
            logger.error(f"Consumer got an unexpected error: {type(e).__name__}: {e}")

        queue.task_done()


async def download_if_not_exist(
        session,
        path,
        url,
        extension=True,
        kwargs=None,
        allowed_extensions=None,
        forbidden_extensions=None,
):
    if kwargs is None:
        kwargs = {}

    if allowed_extensions is None:
        allowed_extensions = []

    allowed_extensions = [item.lower() for item in allowed_extensions + settings.allowed_extensions]
    if "video" in allowed_extensions:
        allowed_extensions += MOVIE_EXTENSIONS

    if forbidden_extensions is None:
        forbidden_extensions = []

    forbidden_extensions = [item.lower() for item in forbidden_extensions + settings.forbidden_extensions]
    if "video" in forbidden_extensions:
        forbidden_extensions += MOVIE_EXTENSIONS

    timeout = aiohttp.ClientTimeout(total=0)
    if os.path.isabs(path):
        absolute_path = path
    else:
        absolute_path = os.path.join(settings.base_path, path)

    drive, nd_path = os.path.splitdrive(absolute_path)
    absolute_path = os.path.join(drive, nd_path.replace(":", ";").replace("|", ""))

    if file_exists(absolute_path, extension):
        return

    file_name = os.path.basename(absolute_path)
    if extension:
        file_extension = get_extension(file_name)
        if allowed_extensions and file_extension.lower() not in allowed_extensions:
            return
        if forbidden_extensions and file_extension.lower() in forbidden_extensions:
            return
        if file_extension.lower() in MOVIE_EXTENSIONS:
            logger.info(f"Starting to download {file_name}")

    async with session.get(url, timeout=timeout, **kwargs) as response:
        response.raise_for_status()

        if not extension:
            disposition = response.headers['content-disposition']
            resp_file_name = re.findall("""filename="(.+).""", disposition)[0]
            absolute_path += "." + get_extension(resp_file_name)
            file_name = os.path.basename(absolute_path)

        Path(os.path.dirname(absolute_path)).mkdir(parents=True, exist_ok=True)

        with open(absolute_path, 'wb') as f:
            while True:
                chunk = await response.content.read(256)
                if not chunk:
                    break
                f.write(chunk)

    start = {
        "name": f"Added new file: '{Fore.GREEN}{{}}{Style.RESET_ALL}'",
        "var": file_name,
        "priority": 100,
        "cut": "back",
    }

    end = {
        "name": " in '{}'",
        "var": os.path.dirname(absolute_path),
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
