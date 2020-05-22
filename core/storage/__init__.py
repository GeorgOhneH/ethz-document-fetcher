import atexit

from core.storage.cache import *

atexit.register(save_jsons)
