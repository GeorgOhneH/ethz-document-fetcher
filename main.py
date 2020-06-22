import asyncio
import logging.config
import os
import ssl
import time
import traceback

import aiohttp
import certifi
import colorama

from core import downloader, template_parser, monitor
from core.utils import user_statistics, check_for_new_release
from core.storage import cache
from settings.logger import LOGGER_CONFIG
from settings.settings import SiteSettings
from settings import global_settings

colorama.init()

logging.config.dictConfig(LOGGER_CONFIG)
logger = logging.getLogger(__name__)


async def main(signals=None, site_settings=None):
    template_path = "template.yml"
    if site_settings is None:
        site_settings = SiteSettings()
    if not site_settings.check_if_valid():
        logger.critical("Settings are not correctly configured. Please run 'python setup.py'. Exiting...")
        return

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)

    async with monitor.MonitorSession(signals=signals, raise_for_status=True, connector=conn,
                                      timeout=aiohttp.ClientTimeout(30)) as session:
        logger.debug(f"Loading template: {template_path}")
        queue = asyncio.Queue()
        producers = []
        template_file = os.path.join(os.path.dirname(__file__), template_path)
        template = template_parser.Template(path=template_file, signals=signals, site_settings=site_settings)
        try:
            template.load()
        except Exception as e:
            if global_settings.loglevel == "DEBUG":
                traceback.print_exc()
            logger.critical(f"A critical error occurred while passing the template: {e}. Exiting...")
            return

        await template.run_root(producers, session, queue)

        user_statistic = asyncio.ensure_future(user_statistics(session, site_settings.username))

        logger.debug(f"Checking for update")
        is_new_release, latest_version, current_version = await check_for_new_release(session)
        if is_new_release:
            logger.info(f"A new update is available. Update with 'git pull'."
                        f" New version: {latest_version}. Current version {current_version}")

        logger.debug("Starting consumers")
        consumers = [asyncio.ensure_future(downloader.download_files(session, queue)) for _ in range(20)]

        logger.debug("Gathering producers")
        await asyncio.gather(*producers)

        logger.debug("Waiting for queue")

        num_unfinished_downloads = queue.qsize() + queue._unfinished_tasks
        if num_unfinished_downloads:
            logger.info(f"Waiting for {num_unfinished_downloads} potential download(s) to finish")
        await queue.join()

        logger.debug("Cancel consumers")
        for c in consumers:
            c.cancel()

        await user_statistic


if __name__ == '__main__':
    start_t = time.time()
    startup_time = time.process_time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    logger.debug(f"Startup time: {startup_time:.2f} seconds")
    logger.debug(f"Total process time: {(time.process_time()):.2f} seconds")
    logger.info(f"Finished in {(time.time() - start_t):.2f} seconds")
