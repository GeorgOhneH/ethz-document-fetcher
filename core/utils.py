import copy
import hashlib
import html
import logging
import os
import re
import shutil

import requests

logger = logging.getLogger(__name__)

LATEST_RELEASE_URL = "https://api.github.com/repos/GeorgOhneH/ethz-document-fetcher/releases/latest"


async def async_user_statistics(session, name):
    if not name:
        return
    data = {
        'name': hashlib.md5(name.encode('utf-8')).hexdigest(),
    }
    try:
        async with session.post("https://ethz-document-fetcher.mikrounix.com/add", data=data) as response:
            pass
    except Exception as e:
        logger.warning(f"Error while tying to post user statistics. Error: {e}")


def user_statistics(name):
    if not name:
        return
    data = {
        'name': hashlib.md5(name.encode('utf-8')).hexdigest(),
    }
    try:
        requests.post("https://ethz-document-fetcher.mikrounix.com/add", data=data)
    except Exception as e:
        logger.warning(f"Error while tying to post user statistics. Error: {e}")


def get_extension_from_response(response):
    disposition = response.headers['content-disposition']
    resp_file_name = re.search("""filename="(.+).""", disposition)[1]
    return get_extension(resp_file_name)


def get_extension(file):
    return file.split(".")[-1]


def split_name_extension(file_name):
    return "".join(file_name.split(".")[:-1]), file_name.split(".")[-1]


def safe_path_join(path, *paths):
    return os.path.join(path, *[safe_path(x) for x in paths if x])


def safe_path(string):
    return html.unescape(string.replace("/", "-").replace("\\", "-")). \
        replace(":", ";").replace("|", "").replace("?", ""). \
        replace("<", "").replace(">", "").replace("*", "")


async def async_get_latest_version(session):
    async with session.get(LATEST_RELEASE_URL) as response:
        data = await response.json()

    return data["tag_name"]


def get_latest_version():
    response = requests.get(LATEST_RELEASE_URL)
    data = response.json()
    return data["tag_name"]


def fit_sections_to_console(*args, filler="..", min_length=10, margin=0):
    min_length = len(filler) + min_length
    c, _ = shutil.get_terminal_size(fallback=(0, 0))
    orig_sections = list(args)
    sections = copy.copy(orig_sections)
    sections.sort(key=lambda s: -s["priority"])

    free = c - sum([len(x["name"]) - 2 for x in sections]) - margin - 6
    length_vars = []
    count = 0
    for section in reversed(sections):
        length_vars.append(count)
        count += min(len(section["var"]), min_length)
    length_vars.reverse()
    if c:
        for length_var, section in zip(length_vars, sections):
            c_free = free - length_var
            if c_free < len(section["var"]) and len(section["var"]) > min_length:
                cut_length = max(c_free, min_length)
                if section["cut"] == "front":
                    section["var"] = (filler + section["var"][-cut_length + len(filler):])
                elif section["cut"] == "back":
                    section["var"] = (section["var"][:cut_length - len(filler)] + filler)

            free -= len(section["var"])

    return "".join([x["name"].format(x["var"]) for x in orig_sections])
