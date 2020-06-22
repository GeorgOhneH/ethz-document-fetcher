import atexit

from core.storage import cache

atexit.register(cache.save_jsons)
