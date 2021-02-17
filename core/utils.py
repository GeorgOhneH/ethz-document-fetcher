import copy
import hashlib
import html
import logging
import os
import re
import shutil
from mimetypes import guess_extension
import functools
from pathlib import Path

import requests
import bs4
from bs4 import BeautifulSoup
from appdirs import user_data_dir

from settings.settings import Settings

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
    if "content-disposition" in response.headers:
        disposition = response.headers['content-disposition']
        resp_file_name_match = re.search("""filename="(.+)\"""", disposition)
        if resp_file_name_match is not None:
            return get_extension(resp_file_name_match[1])

    extension = guess_extension(response.headers['content-type'].partition(';')[0].strip())
    if extension is None:
        return None

    return extension[1:]


def remove_old_files():
    remove_all_temp_files()
    remove_old_log_files()


def remove_all_temp_files():
    for file_name in os.listdir(get_temp_path()):
        path = os.path.join(get_temp_path(), file_name)
        logger.debug(f"Removing temp file/folder: {path}")
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path, ignore_errors=True)


def remove_old_log_files(keep_count=10):
    file_names = [file_name for file_name in os.listdir(get_logs_path()) if file_name.endswith(".log")]
    file_names.sort(reverse=True)
    if len(file_names) <= keep_count:
        return
    for file_name in file_names[keep_count:]:
        path = os.path.join(get_logs_path(), file_name)
        os.remove(path)


def get_extension(file):
    return file.split(".")[-1]


def split_name_extension(file_name):
    return "".join(file_name.split(".")[:-1]), file_name.split(".")[-1]


def safe_path_join(path, *paths):
    return os.path.join(path, *[safe_path(x) for x in paths if x])


def safe_path(string):
    path = html.unescape(string.replace("/", "-").replace("\\", "-")). \
        replace(":", ";").replace("|", "").replace("?", ""). \
        replace("<", "").replace(">", "").replace("*", "")

    return path.strip()


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


@functools.lru_cache(maxsize=None)
def get_app_data_path():
    args = Settings.parser.parse_args()
    if args.app_data_path is not None:
        app_data_path = args.app_data_path
    else:
        app_data_path = user_data_dir("ethz-document-fetcher", appauthor=False, roaming=True)
    Path(app_data_path).mkdir(parents=True, exist_ok=True)
    return app_data_path


@functools.lru_cache(maxsize=None)
def get_temp_path():
    temp_path = os.path.join(get_app_data_path(), "temp")
    Path(temp_path).mkdir(parents=True, exist_ok=True)
    return temp_path


@functools.lru_cache(maxsize=None)
def get_logs_path():
    logs_path = os.path.join(get_app_data_path(), "logs")
    Path(logs_path).mkdir(parents=True, exist_ok=True)
    return logs_path


@functools.lru_cache(maxsize=None)
def get_beautiful_soup_parser():
    try:
        BeautifulSoup("", "lxml")
        return "lxml"
    except bs4.FeatureNotFound:
        logger.warning("Could not find 'lxml'. Falling back to html.parser")
        return "html.parser"

