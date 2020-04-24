import os
from pathlib import Path

BASE_URL = "https://moodle-app2.let.ethz.ch"
AUTH_URL = "https://moodle-app2.let.ethz.ch/auth/shibboleth/login.php"
IDP_DATA = {"idp": "https://aai-logon.ethz.ch/idp/shibboleth"}

MTYPE_FILE = "Datei"
MTYPE_EXTERNAL_LINK = "Link/URL"
MTYPE_DIRECTORY = "Verzeichnis"

CACHE_PATH = os.path.join(os.path.dirname(__file__), "cache")
Path(CACHE_PATH).mkdir(parents=True, exist_ok=True)
