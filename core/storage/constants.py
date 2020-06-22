import os
from pathlib import Path

CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache")
Path(CACHE_PATH).mkdir(parents=True, exist_ok=True)

JSON_CACHE_PATH = os.path.join(CACHE_PATH, "json")
Path(JSON_CACHE_PATH).mkdir(parents=True, exist_ok=True)

FUNCTION_CACHE_PATH = os.path.join(CACHE_PATH, "function_results")
Path(FUNCTION_CACHE_PATH).mkdir(parents=True, exist_ok=True)
