import asyncio
import logging.config
import os

import aiohttp
from colorama import init

import model_parser
from exceptions import ParseModelError
from settings import settings
from downloader import download_files
from utils import user_statistics
from settings.logger import LOGGER_CONFIG

init()

logging.config.dictConfig(LOGGER_CONFIG)
logger = logging.getLogger(__name__)


async def main():
    if not settings.check_if_valid():
        logger.critical("Settings are not correctly configured. Please run 'python setup.py'. Exiting...")
        return

    async with aiohttp.ClientSession(raise_for_status=True) as session:
        await user_statistics(session, settings.username)

        logger.debug(f"Loading model: {settings.model_path}")
        queue = asyncio.Queue()
        producers = []
        model_file = os.path.join(os.path.dirname(__file__), settings.model_path)
        try:
            await model_parser.parse(session, queue, producers, model_file)
        except ParseModelError as e:
            logger.critical(f"An error occurred while passing the model: {e}. Exiting...")
            return

        logger.debug("Starting consumers")
        consumers = [asyncio.create_task(download_files(session, queue)) for _ in range(20)]

        logger.debug("Gathering producers")
        await asyncio.gather(*producers)

        logger.debug("Waiting for queue")
        await queue.join()

        logger.debug("Cancel consumers")
        for c in consumers:
            c.cancel()


if __name__ == '__main__':
    import time

    start_t = time.time()
    startup_time = time.process_time()
    asyncio.run(main())
    logger.debug(f"Startup time: {startup_time:.2f} seconds")
    logger.debug(f"Total process time: {(time.process_time()):.2f} seconds")
    logger.info(f"Finished in {(time.time() - start_t + startup_time):.2f} seconds")
