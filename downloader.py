import os
from pathlib import Path

import aiohttp

import moodle
from settings import settings


async def download_files(session: aiohttp.ClientSession, queue):
    timeout = aiohttp.ClientTimeout(total=0)
    while True:
        item = await queue.get()
        if item.get("absolute_path", False):
            absolute_path = item.get("path")
        else:
            file_path = item.get("path")
            absolute_path = os.path.join(settings.base_path, file_path)

        absolute_path = absolute_path[:3] + absolute_path[3:].replace(":", ";").replace("/", " ").replace("|", "")

        url = item.get("url")
        Path(os.path.dirname(absolute_path)).mkdir(parents=True, exist_ok=True)

        if not os.path.exists(absolute_path):
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                with open(absolute_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(256)
                        if not chunk:
                            break
                        f.write(chunk)

            print(f"Added new file: {os.path.basename(absolute_path)} in '{os.path.dirname(absolute_path)}'")

        queue.task_done()


async def moodle_producer(session, queue, moodle_id, use_cache=False):
    async with session.get(f"https://moodle-app2.let.ethz.ch/course/view.php?id={moodle_id}") as response:
        text = await response.read()
    return await moodle.parse_main_page(session, queue, text, use_cache)


async def custom_producer(func, session, queue):
    return await func(session, queue)


