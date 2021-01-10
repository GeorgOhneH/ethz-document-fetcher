import atexit

import multiprocessing_logging

from core.storage import cache


def _exit():
    multiprocessing_logging.uninstall_mp_handler()
    cache.save_jsons()


atexit.register(_exit)
