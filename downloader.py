import glob
import os
import re
from pathlib import Path

import aiohttp

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

    logger.info(f"Added new file: {file_name} in '{os.path.dirname(absolute_path)}'")


def get_extension(file):
    return file.split(".")[-1]


def file_exists(path, extension):
    if not extension:
        valid_paths = glob.glob(f"{path}.*")
        if len(valid_paths) > 2:
            logger.warning("Found file with same filename, but different extension, could cause problems")

        return len(valid_paths) >= 1

    return os.path.exists(path)
