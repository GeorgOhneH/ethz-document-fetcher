import asyncio
import functools
import pathlib
from urllib.parse import urlparse

import aiohttp
from aiohttp.client import URL

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

    allowed_extensions = set([item.lower() for item in allowed_extensions + site_settings.allowed_extensions])
    if "video" in allowed_extensions:
        allowed_extensions |= MOVIE_EXTENSIONS

    if forbidden_extensions is None:
        forbidden_extensions = []

    forbidden_extensions = set([item.lower() for item in forbidden_extensions + site_settings.forbidden_extensions])
    if "video" in forbidden_extensions:
        forbidden_extensions |= MOVIE_EXTENSIONS

    forbidden_extensions -= allowed_extensions

    if isinstance(url, str):
        url = URL(url)

    domain = url.host

    timeout = aiohttp.ClientTimeout(total=0)
    if os.path.isabs(path):
        raise ValueError("Absolutes paths are not allowed")

    absolute_path = os.path.join(site_settings.base_path, path)

    if not with_extension:
        guess_extension = await cache.check_extension(session, str(url), session_kwargs=session_kwargs)
        if guess_extension is None:
            logger.warning(f"Could not retrieve the extension for {url}")
            return

        absolute_path += "." + guess_extension

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

    file_name = os.path.basename(absolute_path)
    file_extension = get_extension(file_name)
    if allowed_extensions and file_extension.lower() not in allowed_extensions:
        return
    if file_extension.lower() in forbidden_extensions:
        return

    async with session.get(url, timeout=timeout, **session_kwargs) as response:
        response.raise_for_status()
        response_headers = response.headers

        if response.status == 304:
            logger.debug(f"File '{absolute_path}' not modified")
            cache.save_checksum(absolute_path, checksum)
            return

        if file_extension.lower() in MOVIE_EXTENSIONS:
            logger.info(f"Starting to download {file_name}")

        pathlib.Path(os.path.dirname(absolute_path)).mkdir(parents=True, exist_ok=True)

        if action == ACTION_REPLACE and site_settings.keep_replaced_files:
            dir_path = os.path.dirname(absolute_path)
            pure_name, extension = split_name_extension(file_name)
            old_file_name = f"{pure_name}-old.{extension}"
            old_absolute_path = os.path.join(dir_path, old_file_name)
            os.replace(absolute_path, old_absolute_path)

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
            raise e

    if site_settings.highlight_difference and \
            action == ACTION_REPLACE and \
            site_settings.keep_replaced_files and \
            file_extension.lower() == "pdf":
        logger.debug(f"Adding highlights to {absolute_path}")

        temp_file_name = f"{pure_name}-temp.{extension}"
        temp_absolute_path = os.path.join(dir_path, temp_file_name)

        future = cancellable_pool.apply(
            functools.partial(pdf_highlighter.add_differ_highlight,
                              new_path=absolute_path,
                              old_path=old_absolute_path,
                              out_path=temp_absolute_path)
        )
        try:
            await future
            os.replace(temp_absolute_path, old_absolute_path)
        except asyncio.CancelledError as e:
            os.replace(old_absolute_path, absolute_path)
            logger.debug(f"Reverted old file {absolute_path}")
            raise e
        except Exception as e:
            logger.warning(f"Could not add pdf highlight to {absolute_path}. {type(e).__name__}: {e}")
            signal_handler.got_warning(unique_key,
                                       f"Could not add pdf highlight to {absolute_path}. {type(e).__name__}: {e}")
        finally:
            if os.path.exists(temp_absolute_path):
                logger.debug(f"Removed temp file {temp_absolute_path}")
                os.remove(temp_absolute_path)

    if "ETag" in response_headers:
        cache.save_etag(absolute_path, response.headers["ETag"])
    elif domain not in FORCE_DOWNLOAD_BLACKLIST:
        logger.warning(f"url: {url} had not an etag and is not in the blacklist")

    cache.save_checksum(absolute_path, checksum)

    if action == ACTION_REPLACE:
        if site_settings.keep_replaced_files and os.path.exists(old_absolute_path):
            signal_handler.replaced_file(unique_key, absolute_path, old_absolute_path)
        else:
            signal_handler.replaced_file(unique_key, absolute_path)
        method_msg = "Replaced"
    elif action == ACTION_NEW:
        signal_handler.added_new_file(unique_key, absolute_path)
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
