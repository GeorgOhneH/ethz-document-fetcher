import os
from pathlib import Path
from settings import settings

BASE_URL = "https://video.ethz.ch/lectures/"

ETH_AUTH = {
    "_charset_": "utf-8",
    "j_username": settings.username,
    "j_password": settings.password,
    "j_validate": "true",
}

CACHE_PATH = os.path.join(os.path.dirname(__file__), "cache")
Path(CACHE_PATH).mkdir(parents=True, exist_ok=True)
