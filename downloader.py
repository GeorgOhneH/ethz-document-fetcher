import os
from pathlib import Path

import aiohttp

import moodle
from settings import settings


async def download_files(session: aiohttp.ClientSession, queue):
    while True:
        item = await queue.get()
        kwargs = item.get("kwargs", {})
        file_path = item.get("path")
        url = item.get("url")

        await download_if_not_exist(session, file_path, url, kwargs)

        queue.task_done()


async def download_if_not_exist(session, file_path, url, kwargs=None):
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

    if not os.path.exists(absolute_path):
        file_name = os.path.basename(absolute_path)
        extension = file_name.split(".")[-1]
        if extension.lower() in ["mp4", "webm", "avi", "mkv", "mov", "m4v"]:
            if not settings.download_videos:
                return
            print(f"Starting to download {file_name}")

        async with session.get(url, timeout=timeout, **kwargs) as response:
            response.raise_for_status()
            with open(absolute_path, 'wb') as f:
                while True:
                    chunk = await response.content.read(256)
                    if not chunk:
                        break
                    f.write(chunk)

        print(f"Added new file: {file_name} in '{os.path.dirname(absolute_path)}'")
