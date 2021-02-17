import asyncio

from core.utils import safe_path_join
from settings.config import ConfigString
from .constants import *

GDRIVE_ID_CONFIG = ConfigString(gui_name="ID")


def _get_download_params(file_id):
    return {
        "export": "download",
        "id": file_id,
    }


def _get_file_url(file_id):
    return f"{BASE_URL}files/{file_id}"


def _get_folder_params(file_id):
    return {
        "q": f"'{file_id}' in parents",
        "fields": "nextPageToken,files(name,size,id,mimeType,modifiedTime)",
        "pageSize": "1000",
        **DEFAULT_PARAMS
    }


async def parse_folder(session, queue, base_path, file_id):
    params = _get_folder_params(file_id)

    async with session.get(FOLDER_URL, params=params, headers=REFERER_HEADERS) as response:
        data = await response.json()

    files = data["files"]
    while "nextPageToken" in data:
        page_params = {"pageToken": data["nextPageToken"], **params}
        async with session.get(FOLDER_URL, params=page_params, headers=REFERER_HEADERS) as response:
            data = await response.json()
        files += data["files"]

    tasks = []
    for file in files:
        path = safe_path_join(base_path, file["name"])
        if file["mimeType"] == MIMETYPE_FOLDER:
            tasks.append(parse_folder(session, queue, path, file["id"]))

    await asyncio.gather(*tasks)

    for file in files:
        with_extension = False
        path = safe_path_join(base_path, file["name"])

        if file["mimeType"] == MIMETYPE_GOOGLE_DOCS:
            url = f"https://docs.google.com/document/d/{file['id']}/export"
            params = {"format": "docx"}
        elif file["mimeType"] == MIMETYPE_DRAWING:
            url = f"https://docs.google.com/drawings/d/{file['id']}/export/png"
            params = {}
        elif file["mimeType"] == MIMETYPE_PRESENTATION:
            url = f"https://docs.google.com/presentation/d/{file['id']}/export/pptx"
            params = {}
        elif file["mimeType"] == MIMETYPE_JAM:
            url = "https://jamboard.google.com/export"
            params = {"id": file["id"]}
        elif file["mimeType"] == MIMETYPE_SPREADSHEET:
            url = f"https://docs.google.com/spreadsheets/d/{file['id']}/export"
            params = {"format": "xlsx"}
        elif "application/vnd.google-apps" in file["mimeType"]:
            continue

        else:
            url = "https://drive.google.com/uc"
            params = _get_download_params(file["id"])
            with_extension = True

        await queue.put({"url": url,
                         "path": path,
                         "checksum": file["modifiedTime"],
                         "session_kwargs": {"params": params},
                         "with_extension": with_extension,
                         })


async def producer(session,
                   queue,
                   base_path,
                   download_settings,
                   file_id: GDRIVE_ID_CONFIG):
    await parse_folder(session, queue, base_path, file_id)


async def get_folder_name(session, file_id, **kwargs):
    async with session.get(_get_file_url(file_id), params=META_PARAMS, headers=REFERER_HEADERS) as response:
        file = await response.json()

    if file["mimeType"] != MIMETYPE_FOLDER:
        raise ValueError("Only supports folder")

    return file["name"]
