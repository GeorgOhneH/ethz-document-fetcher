import asyncio
import os
from pathlib import Path

import moodle
import settings


async def download_files(session, queue):
    while True:
        item = await queue.get()
        file_path = item.get("path").replace(":", ";").replace("/", " ").replace("|", "")
        absolute_path = os.path.join(settings.base_path, file_path)
        url = item.get("url")
        Path(os.path.dirname(absolute_path)).mkdir(parents=True, exist_ok=True)

        if not os.path.exists(absolute_path):
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()

            with open(absolute_path, 'wb') as f:
                f.write(content)

            print("Added new file: {} in '{}'".format(os.path.basename(file_path), file_path))

        queue.task_done()


async def moodle_producer(session, queue, moodle_id, use_cache=False):
    async with session.get(f"https://moodle-app2.let.ethz.ch/course/view.php?id={moodle_id}") as response:
        text = await response.read()
    return await moodle.parse_main_page(session, queue, text, use_cache)


async def custom_producer(func, session, queue):
    return await func(session, queue)


