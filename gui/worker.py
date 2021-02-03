import asyncio
import logging.config
import ssl
import time

import aiohttp
import certifi
from PyQt5.QtCore import *

from core import downloader, template_parser, monitor
from core.cancellable_pool import CancellablePool
from core import unique_queue
from core.utils import remove_all_temp_files

logger = logging.getLogger(__name__)


class Signals(QObject):
    finished = pyqtSignal()
    stopped = pyqtSignal()

    site_started = pyqtSignal([str], [str, str])
    site_finished = pyqtSignal([str], [str, str])
    got_warning = pyqtSignal([str], [str, str])
    got_error = pyqtSignal([str], [str, str])

    update_folder_name = pyqtSignal([str, str])
    update_base_path = pyqtSignal([str, str])

    added_new_file = pyqtSignal([str, str])
    replaced_file = pyqtSignal([str, str, str, str])

    downloaded_content_length = pyqtSignal(int)


class Worker(QObject):
    def __init__(self):
        super().__init__()
        self.signals = Signals()

        self.unique_keys = ["root"]
        self.recursive = True
        self.site_settings = None
        self.template_path = None

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.tasks = None

    @pyqtSlot()
    def main(self):
        try:
            start_t = time.time()
            logger.info(f"Starting worker")
            self.tasks = self.loop.create_task(self.run(self.signals))
            self.loop.run_until_complete(self.tasks)
            logger.info(f"Finished in {(time.time() - start_t):.2f} seconds")
        except Exception as e:
            logger.error(f"Unexpected error. {type(e).__name__}: {e}", exc_info=True)
        finally:
            self.tasks = None
            self.loop.run_until_complete(asyncio.sleep(0))
            for task in asyncio.all_tasks(loop=self.loop):  # clean up not finished tasks
                task.cancel()
                try:
                    self.loop.run_until_complete(task)
                except BaseException as e:
                    pass
            self.signals.finished.emit()

    def stop(self):
        if self.tasks is not None:
            self.signals.stopped.emit()
            self.tasks.cancel()

    async def run(self, signals=None):
        if not self.site_settings.check_if_valid():
            logger.critical("Settings are not correctly configured.")
            return

        remove_all_temp_files()

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        conn = aiohttp.TCPConnector(ssl=ssl_context,
                                    limit=self.site_settings.conn_limit,
                                    limit_per_host=self.site_settings.conn_limit_per_host)

        async with monitor.MonitorSession(signals=signals, raise_for_status=True, connector=conn,
                                          timeout=aiohttp.ClientTimeout(30)) as session:

            try:
                logger.debug(f"Loading template: {self.template_path}")
                queue = unique_queue.UniqueQueue()
                producers = []
                cancellable_pool = CancellablePool()
                template = template_parser.Template(path=self.template_path,
                                                    signals=signals)
                try:
                    template.load()
                except asyncio.CancelledError as e:
                    raise e
                except Exception as e:
                    logger.critical(f"A critical error occurred while passing the template: {e}. Exiting...")
                    return

                logger.debug("Starting consumers")
                consumers = [asyncio.ensure_future(downloader.download_files(session, queue)) for _ in range(20)]

                await template.run_from_unique_keys(self.unique_keys,
                                                    producers=producers,
                                                    session=session,
                                                    queue=queue,
                                                    site_settings=self.site_settings,
                                                    cancellable_pool=cancellable_pool,
                                                    recursive=self.recursive)

                logger.debug("Gathering producers")
                await asyncio.gather(*producers)

                logger.debug("Waiting for queue")
                await queue.join()

            except asyncio.CancelledError:
                return

            finally:
                logger.debug("Cancel producers")
                for p in producers:
                    p.cancel()

                logger.debug("Cancel consumers")
                for c in consumers:
                    c.cancel()

                logger.debug("Clearing queue")
                while not queue.empty():
                    item = queue.get_nowait()
                    queue.task_done()
                    signals.site_finished[str].emit(item["unique_key"])

                logger.debug("Shutting down worker pool")
                cancellable_pool.shutdown()
