# API key from https://github.com/Akianonymus/gdrive-downloader/tree/master
API_KEY = "AIzaSyD2dHsZJ9b4OXuy5B_owiL8W18NaNOM8tk"

BASE_URL = "https://www.googleapis.com/drive/v3/"

FOLDER_URL = f"{BASE_URL}files"

MIMETYPE_FOLDER = "application/vnd.google-apps.folder"
MIMETYPE_GOOGLE_DOCS = "application/vnd.google-apps.document"
MIMETYPE_DRAWING = "application/vnd.google-apps.drawing"
MIMETYPE_FORM = "application/vnd.google-apps.form"
MIMETYPE_FUSION_TABLE = "application/vnd.google-apps.fusiontable"
MIMETYPE_MAP = "application/vnd.google-apps.map"
MIMETYPE_PRESENTATION = "application/vnd.google-apps.presentation"
MIMETYPE_SCRIPT = "application/vnd.google-apps.script"
MIMETYPE_SITE = "application/vnd.google-apps.site"
MIMETYPE_SPREADSHEET = "application/vnd.google-apps.spreadsheet"
MIMETYPE_JAM = "application/vnd.google-apps.jam"


DEFAULT_PARAMS = {
    "key": API_KEY,
    "supportsAllDrives": "true",
    "includeItemsFromAllDrives": "true",

}


META_PARAMS = {
    "alt": "json",
    "fields": "name,size,mimeType,modifiedTime",
    **DEFAULT_PARAMS
}

REFERER_HEADERS = {
    "referer": "https://drive.google.com",
}
