import asyncio
import logging.config
import os
import ssl
import time

import aiohttp
import certifi
import colorama

from core import download_files, parse_template
from core.exceptions import ParseTemplateError
from core.utils import user_statistics, check_for_new_release
from settings import settings
from settings.logger import LOGGER_CONFIG

colorama.init()

logging.config.dictConfig(LOGGER_CONFIG)
logger = logging.getLogger(__name__)


async def main():
    if not settings.check_if_valid():
        logger.critical("Settings are not correctly configured. Please run 'python setup.py'. Exiting...")
        return

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)

    async with aiohttp.ClientSession(raise_for_status=True, connector=conn) as session:
        logger.debug(f"Loading template: {settings.template_path}")
        queue = asyncio.Queue()
        producers = []
        template_file = os.path.join(os.path.dirname(__file__), settings.template_path)
        try:
            await parse_template(session, queue, producers, template_file)
        except ParseTemplateError as e:
            logger.critical(f"A critical error occurred while passing the template: {e}. Exiting...")
            for p in producers:
                p.cancel()
            return

        user_statistic = asyncio.create_task(user_statistics(session, settings.username))

        logger.debug(f"Checking for update")
        is_new_release, latest_version, current_version = await check_for_new_release(session)
        if is_new_release:
            logger.info(f"A new update is available. Update with 'git pull'."
                        f" New version: {latest_version}. Current version {current_version}")

        logger.debug("Starting consumers")
        consumers = [asyncio.create_task(download_files(session, queue)) for _ in range(20)]

        logger.debug("Gathering producers")
        await asyncio.gather(*producers)

        logger.debug("Waiting for queue")
        await queue.join()

        logger.debug("Cancel consumers")
        for c in consumers:
            c.cancel()

        await user_statistic


if __name__ == '__main__':
    start_t = time.time()
    startup_time = time.process_time()
    asyncio.run(main(), debug=False)
    logger.debug(f"Startup time: {startup_time:.2f} seconds")
    logger.debug(f"Total process time: {(time.process_time()):.2f} seconds")
    logger.info(f"Finished in {(time.time() - start_t + startup_time):.2f} seconds")
