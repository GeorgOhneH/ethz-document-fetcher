import asyncio
import logging.config
import os
import ssl
import time
from multiprocessing import freeze_support

import aiohttp
import certifi
import colorama

from core import unique_queue
from core import downloader, template_parser, monitor
from core.cancellable_pool import CancellablePool
from core.constants import VERSION
from core.utils import async_user_statistics, async_get_latest_version, remove_old_files
from settings.logger import setup_logger
from settings.settings import DownloadSettings, TemplatePathSettings, BehaviorSettings

logger = logging.getLogger(__name__)


async def main(signals=None, download_settings=None):
    behavior_settings = BehaviorSettings()
    setup_logger(behavior_settings.loglevel)

    template_path = TemplatePathSettings().template_path

    if download_settings is None:
        download_settings = DownloadSettings()
    if not download_settings.check_if_valid():
        logger.critical("Settings are not correctly configured. "
                        "Please run 'python main.py --help' for more info. "
                        "Exiting...")
        return

    remove_old_files()

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context,
                                limit=download_settings.conn_limit,
                                limit_per_host=download_settings.conn_limit_per_host)
    timeout = aiohttp.ClientTimeout(total=30, sock_connect=5)
    async with monitor.MonitorSession(signals=signals, raise_for_status=True, connector=conn,
                                      timeout=timeout) as session:
        logger.debug(f"Loading template: {template_path}")
        queue = unique_queue.UniqueQueue()
        producers = []
        cancellable_pool = CancellablePool()
        template_file = os.path.join(os.path.dirname(__file__), template_path)
        template = template_parser.Template(path=template_file, signals=signals)
        try:
            template.load()
        except Exception as e:
            logger.critical(f"A critical error occurred while passing the template."
                            f" {type(e).__name__}: {e}. Exiting...", exc_info=True)
            return

        await template.run_root(producers,
                                session,
                                queue,
                                download_settings=download_settings,
                                cancellable_pool=cancellable_pool)

        user_statistic = asyncio.ensure_future(async_user_statistics(session, download_settings.username))

        logger.debug(f"Checking for update")
        latest_version = await async_get_latest_version(session)
        if latest_version != VERSION and behavior_settings.check_for_updates:
            logger.info(f"A new update is available. Update with 'git pull'."
                        f" New version: {latest_version}. Current version {VERSION}")

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

        cancellable_pool.shutdown()

        await user_statistic


if __name__ == '__main__':
    freeze_support()
    colorama.init()

    start_t = time.time()
    startup_time = time.process_time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    logger.debug(f"Startup time: {startup_time:.2f} seconds")
    logger.debug(f"Total process time: {(time.process_time()):.2f} seconds")
    logger.info(f"Finished in {(time.time() - start_t):.2f} seconds")
