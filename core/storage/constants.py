import os
from pathlib import Path

from core.constants import APP_DATA_PATH

CACHE_PATH = os.path.join(APP_DATA_PATH, "cache")
Path(CACHE_PATH).mkdir(parents=True, exist_ok=True)

JSON_CACHE_PATH = os.path.join(CACHE_PATH, "json")
Path(JSON_CACHE_PATH).mkdir(parents=True, exist_ok=True)

FUNCTION_CACHE_PATH = os.path.join(CACHE_PATH, "function_results")
Path(FUNCTION_CACHE_PATH).mkdir(parents=True, exist_ok=True)
