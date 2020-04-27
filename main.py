import asyncio
import logging.config
import os

import aiohttp
from colorama import init

import model_parser
from settings import settings
from downloader import download_files
from utils import user_statistics
from settings.logger import LOGGER_CONFIG

init()

logging.config.dictConfig(LOGGER_CONFIG)
logger = logging.getLogger(__name__)


async def main():
    if not settings.check_if_set():
        raise ValueError("Please run 'python setup.py'")

    async with aiohttp.ClientSession(raise_for_status=True) as session:
        await user_statistics(session, settings.username)

        logger.debug(f"Loading model: {settings.model_path}")
        queue = asyncio.Queue()
        producers = []
        model_file = os.path.join(os.path.dirname(__file__), settings.model_path)
        await model_parser.parse(session, queue, producers, model_file)

        logger.debug("Starting consumers")
        consumers = [asyncio.create_task(download_files(session, queue)) for _ in range(20)]

        logger.debug("Gathering producers")
        await asyncio.gather(*producers)

        logger.debug("Waiting for queue")
        await queue.join()

        for c in consumers:
            c.cancel()


if __name__ == '__main__':
    import time

    start_t = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    logger.info(f"Finished in {(time.time() - start_t):.2f} seconds")
