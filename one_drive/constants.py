import os
from pathlib import Path

CACHE_PATH = os.path.join(os.path.dirname(__file__), "cache")
Path(CACHE_PATH).mkdir(parents=True, exist_ok=True)
