import asyncio
import functools
import pathlib
from urllib.parse import urlparse
import itertools
import random
import shutil

import aiohttp
from aiohttp.client import URL
import fitz

from core import pdf_highlighter
from core.constants import *
from core.storage import cache
from core.utils import get_extension, fit_sections_to_console, split_name_extension

logger = logging.getLogger(__name__)


async def download_files(session: aiohttp.ClientSession, queue):
    while True:
        item = await queue.get()
        unique_key = item["unique_key"]
        signal_handler = item["signal_handler"]
        try:
            await download_if_not_exist(session, **item)
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Consumer got an unexpected error: {type(e).__name__}: {e}", exc_info=True)
            signal_handler.got_error(unique_key,
                                     f"Could not download file from url: {item['url']}. {type(e).__name__}: {e}")

        finally:
            signal_handler.finished(unique_key)
            queue.task_done()


def merge_extension_filter(extensions):
    merged_extensions = set([item.lower() for item in extensions])
    if "video" in merged_extensions:
        merged_extensions |= MOVIE_EXTENSIONS
    return merged_extensions


def is_extension_forbidden(extension, allowed_extensions, forbidden_extensions):
    allowed_extensions = merge_extension_filter(allowed_extensions)
    forbidden_extensions = merge_extension_filter(forbidden_extensions)

    forbidden_extensions -= allowed_extensions

    if allowed_extensions and extension.lower() not in allowed_extensions:
        return True
    if extension.lower() in forbidden_extensions:
        return True

    return False


async def download_if_not_exist(session,
                                path,
                                url,
                                site_settings,
                                cancellable_pool,
                                with_extension=True,
                                session_kwargs=None,
                                allowed_extensions=None,
                                forbidden_extensions=None,
                                checksum=None,
                                signal_handler=None,
                                unique_key=None):
    if session_kwargs is None:
        session_kwargs = {}

    if allowed_extensions is None:
        allowed_extensions = []

    if forbidden_extensions is None:
        forbidden_extensions = []

    allowed_extensions += site_settings.allowed_extensions
    forbidden_extensions += site_settings.forbidden_extensions

    if isinstance(url, str):
        url = URL(url)

    domain = url.host

    if os.path.isabs(path):
        raise ValueError("Absolutes paths are not allowed")

    absolute_path = os.path.join(site_settings.base_path, path)

    if not with_extension:
        guess_extension = await cache.check_extension(session, str(url), session_kwargs=session_kwargs)
        if guess_extension is None:
            logger.warning(f"Could not retrieve the extension for {url}")
            return

        absolute_path += "." + guess_extension

    file_name = os.path.basename(absolute_path)
    file_extension = get_extension(file_name)

    dir_path = os.path.dirname(absolute_path)
    pure_name, extension = split_name_extension(file_name)

    temp_file_name = f"{random.getrandbits(64)}.{extension}"
    temp_absolute_path = os.path.join(TEMP_PATH, temp_file_name)

    old_file_name = f"{pure_name}-old.{extension}"
    old_absolute_path = os.path.join(dir_path, old_file_name)

    diff_file_name = f"{pure_name}-diff.{extension}"
    diff_absolute_path = os.path.join(dir_path, diff_file_name)

    force = False
    if checksum is not None:
        force = not cache.is_checksum_same(absolute_path, checksum)
    elif site_settings.force_download and domain not in FORCE_DOWNLOAD_BLACKLIST:
        force = True

    if os.path.exists(absolute_path) and not force:
        return

    if os.path.exists(absolute_path):
        headers = session_kwargs.get("headers", {})
        etag = cache.get_etag(absolute_path)
        if etag is not None:
            headers["If-None-Match"] = etag
        if headers:
            session_kwargs["headers"] = headers

    if os.path.exists(absolute_path):
        action = ACTION_REPLACE
    else:
        action = ACTION_NEW

    if is_extension_forbidden(extension=file_extension,
                              forbidden_extensions=forbidden_extensions,
                              allowed_extensions=allowed_extensions):
        return

    try:

        async with session.get(url, timeout=aiohttp.ClientTimeout(total=0), **session_kwargs) as response:
            response.raise_for_status()
            response_headers = response.headers

            if response.status == 304:
                logger.debug(f"File '{absolute_path}' not modified")
                cache.save_checksum(absolute_path, checksum)
                return

            if file_extension.lower() in MOVIE_EXTENSIONS:
                logger.info(f"Starting to download {file_name}")

            pathlib.Path(os.path.dirname(absolute_path)).mkdir(parents=True, exist_ok=True)

            if action == ACTION_REPLACE:
                shutil.move(absolute_path, temp_absolute_path)

            try:
                with open(absolute_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
            except BaseException as e:
                os.remove(absolute_path)
                logger.debug(f"Removed file {absolute_path}")
                if action == ACTION_REPLACE:
                    logger.debug(f"Reverting temp file to new file: {absolute_path}")
                    shutil.move(temp_absolute_path, absolute_path)
                raise e

        if site_settings.highlight_difference and \
                action == ACTION_REPLACE and \
                file_extension.lower() == "pdf":
            await _add_pdf_highlights(site_settings=site_settings,
                                      cancellable_pool=cancellable_pool,
                                      signal_handler=signal_handler,
                                      unique_key=unique_key,
                                      absolute_path=absolute_path,
                                      old_absolute_path=temp_absolute_path,
                                      out_path=diff_absolute_path)

        if action == ACTION_REPLACE and site_settings.keep_replaced_files:
            shutil.move(temp_absolute_path, old_absolute_path)

        if "ETag" in response_headers:
            cache.save_etag(absolute_path, response.headers["ETag"])
        elif domain not in FORCE_DOWNLOAD_BLACKLIST:
            logger.warning(f"url: {url} had not an etag and is not in the blacklist")

        cache.save_checksum(absolute_path, checksum)

        if action == ACTION_REPLACE:
            signal_old_path, signal_diff_path = None, None
            if os.path.exists(old_absolute_path) and site_settings.keep_replaced_files:
                signal_old_path = old_absolute_path
            if os.path.exists(diff_absolute_path) and site_settings.highlight_difference:
                signal_diff_path = diff_absolute_path

            signal_handler.replaced_file(unique_key,
                                         absolute_path,
                                         signal_old_path,
                                         signal_diff_path)
        elif action == ACTION_NEW:
            signal_handler.added_new_file(unique_key, absolute_path)

        if action == ACTION_REPLACE:
            method_msg = "Replaced"
        elif action == ACTION_NEW:
            method_msg = "Added new"
        else:
            method_msg = "Unexpected action"

        start = {
            "name": f"{method_msg} file: '{{}}'",
            "var": file_name,
            "priority": 100,
            "cut": "back",
        }

        end = {
            "name": " in '{}'",
            "var": os.path.dirname(absolute_path),
            "priority": -100,
            "cut": "front",
        }

        logger.info(fit_sections_to_console(start, end, margin=1))

    finally:
        if os.path.exists(temp_absolute_path):
            os.remove(temp_absolute_path)


async def _add_pdf_highlights(site_settings,
                              cancellable_pool,
                              signal_handler,
                              unique_key,
                              absolute_path,
                              old_absolute_path,
                              out_path):
    if site_settings.highlight_page_limit != 0:
        with fitz.Document(old_absolute_path, filetype="pdf") as doc:
            if doc.pageCount > site_settings.highlight_page_limit:
                logger.debug(f"Skipping highlights. File: {absolute_path}. Page Count: {doc.pageCount} is to large")
                return

    logger.debug(f"Adding highlights to {absolute_path}")

    future = cancellable_pool.apply(
        functools.partial(pdf_highlighter.add_differ_highlight,
                          new_path=absolute_path,
                          old_path=old_absolute_path,
                          out_path=out_path)
    )
    try:
        await future
    except asyncio.CancelledError as e:
        if os.path.exists(out_path):
            logger.debug(f"Removed out file {out_path}")
            os.remove(out_path)
        raise e
    except Exception as e:
        if os.path.exists(out_path):
            logger.debug(f"Removed out file {out_path}")
            os.remove(out_path)
        logger.warning(f"Could not add pdf highlight to {absolute_path}. {type(e).__name__}: {e}")
        signal_handler.got_warning(unique_key,
                                   f"Could not add pdf highlight to {absolute_path}. {type(e).__name__}: {e}")
