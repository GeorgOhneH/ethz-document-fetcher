import atexit

from core.storage import cache


def _exit():
    cache.save_jsons()


atexit.register(_exit)
