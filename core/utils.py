import hashlib
import html
import logging
import os
import re
from pathlib import Path


logger = logging.getLogger(__name__)


async def user_statistics(session, name):
    if not name:
        return
    data = {
        'name': hashlib.md5(name.encode('utf-8')).hexdigest(),
    }
    async with session.post("https://ethz-document-fetcher.mikrounix.com/add", data=data) as response:
        pass


def get_extension_from_response(response):
    disposition = response.headers['content-disposition']
    resp_file_name = re.search("""filename="(.+).""", disposition)[1]
    return get_extension(resp_file_name)


def get_extension(file):
    return file.split(".")[-1]


def split_name_extension(file_name):
    "".join(file_name.split(".")[:-1]), file_name.split(".")[-1]


def save_txt(section, path):
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "w+") as f:
        f.write(str(section))


def load_txt(path):
    with open(path, "r") as f:
        return f.read()


def safe_path_join(path, *paths):
    return os.path.join(path, *[safe_path(x) for x in paths if x])


def safe_path(string):
    return html.unescape(string.replace("/", "-")).replace(":", ";").replace("|", "")


async def check_for_new_release(session):
    main_path = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(main_path, "version.txt")
    with open(path) as f:
        current_version = f.readline().strip()

    async with session.get("https://api.github.com/repos/GeorgOhneH/ethz-document-fetcher/releases/latest") as response:
        data = await response.json()

    latest_version = data["tag_name"]
    c_v_i = [int(x) for x in current_version[1:].split(".")]
    l_v_i = [int(x) for x in latest_version[1:].split(".")]
    for i, latest_i in enumerate(l_v_i):
        current_i = c_v_i[i] if i < len(c_v_i) else 0
        if latest_i > current_i:
            return True, latest_version, current_version
        elif latest_i < current_i:
            return False, latest_version, current_version
    return False, latest_version, current_version



