from settings import settings

BASE_URL = "https://video.ethz.ch/lectures/"

ETH_AUTH = {
    "_charset_": "utf-8",
    "j_username": settings.username,
    "j_password": settings.password,
    "j_validate": "true",
}

