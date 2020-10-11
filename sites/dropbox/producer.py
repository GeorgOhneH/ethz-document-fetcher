import asyncio
from urllib.parse import urlparse

from core.utils import safe_path_join

from .constants import DEFAULT_COOKIE, LIST_ENTRIES_URL, TIME_COOKIE_VALUE


def _split_url(url):
    parts = [part.strip() for part in urlparse(url).path.split("/") if part.strip() != ""]
    if parts[0] != "sh":
        return ValueError("Only works with shared links")

    key, secure_hash = parts[1:3]
    sub_path = "/".join(parts[3:])

    return key, secure_hash, sub_path


async def get_folder_name(session, url, **kwargs):
    key, secure_hash, sub_path = _split_url(url)
    data = _get_data(key, secure_hash, sub_path)

    async with session.post(LIST_ENTRIES_URL, cookies=DEFAULT_COOKIE, data=data) as response:
        result = await response.json()

    return result["folder_shared_link_info"]["displayName"]


def _get_data(key, secure_hash, sub_path=""):
    return {
        "is_xhr": "true",
        't': TIME_COOKIE_VALUE,
        'link_key': key,
        'link_type': "s",
        'secure_hash': secure_hash,
        'sub_path': sub_path
    }


async def producer(session, queue, base_path, site_settings, url):
    key, secure_hash, sub_path = _split_url(url=url)

    cut_path = len([x for x in sub_path.split("/") if x.strip() != ""])

    await parse_folder(session,
                       queue,
                       base_path,
                       site_settings,
                       key,
                       secure_hash,
                       sub_path=sub_path,
                       cut_path_num=cut_path)


async def parse_folder(session, queue, base_path, site_settings, key, secure_hash, sub_path, cut_path_num=0):
    data = _get_data(key, secure_hash, sub_path)

    async with session.post(LIST_ENTRIES_URL, cookies=DEFAULT_COOKIE, data=data) as response:
        result = await response.json()

    tasks = []

    for entry, share_tokens in zip(result["entries"], result["share_tokens"]):
        if entry["is_dir"]:
            coroutine = parse_folder(session=session,
                                     queue=queue,
                                     base_path=base_path,
                                     site_settings=site_settings,
                                     key=share_tokens["linkKey"],
                                     secure_hash=share_tokens["secureHash"],
                                     sub_path=share_tokens["subPath"],
                                     cut_path_num=cut_path_num)
            tasks.append(asyncio.create_task(coroutine))
            continue

        checksum = entry["sjid"]
        href = entry["href"]
        url = href.replace("dl=0", "dl=1")

        sub_path = share_tokens["subPath"]

        path = safe_path_join(base_path, *sub_path.split("/")[cut_path_num + 1:])

        await queue.put({"url": url,
                         "path": path,
                         "checksum": checksum,
                         })

    await asyncio.gather(*tasks)
