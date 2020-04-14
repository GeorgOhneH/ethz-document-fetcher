import os
from pathlib import Path

BASE_URL = "https://moodle-app2.let.ethz.ch"
AUTH_URL = "https://moodle-app2.let.ethz.ch/auth/shibboleth/login.php"
IDP_DATA = {"idp": "https://aai-logon.ethz.ch/idp/shibboleth"}

PDF_IMG = "https://moodle-app2.let.ethz.ch/theme/image.php/boost_ethz/core/1579733031/f/pdf-24"
FOLDER_IMG = "https://moodle-app2.let.ethz.ch/theme/image.php/boost_ethz/folder/1579733031/icon"
SUB_FOLDER_IMG = "https://moodle-app2.let.ethz.ch/theme/image.php/boost_ethz/core/1579733031/f/folder-24"
EXTERNAL_LINK_IMG = "https://moodle-app2.let.ethz.ch/theme/image.php/boost_ethz/url/1579733031/icon"

MTYPE_FILE = "Datei"
MTYPE_EXTERNAL_LINK = "Link/URL"
MTYPE_DIRECTORY = "Verzeichnis"

CACHE_PATH = os.path.join(os.path.dirname(__file__), "cache")
Path(CACHE_PATH).mkdir(parents=True, exist_ok=True)
