import atexit

import multiprocessing_logging

from core.storage import cache


from core import multiprocess_logger


def _exit():
    multiprocess_logger.uninstall_mp_handler()
    cache.save_jsons()


atexit.register(_exit)
