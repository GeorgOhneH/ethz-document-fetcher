import re
import asyncio

from aiohttp.client import URL
from bs4 import BeautifulSoup

from core.constants import BEAUTIFUL_SOUP_PARSER
from core.utils import safe_path_join


def _get_page_meta(html, keys):
    possible_keys = set(keys)
    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)
    result = {}

    for line in str(soup.findChildren("script")).split(','):
        for key in possible_keys:
            if key in line:
                if "\"" in line:
                    value = line.split("\"")[1]
                else:
                    value = line.split("'")[1]
                result[key] = value.strip()
                possible_keys.remove(key)
                break

    return result


async def download(session, queue, base_path, url, password=None, file_name=None):
    domain = re.match(r"https?://([^.]*\.?)zoom.us", url).group(1)

    agent_header = {
        "referer": f"https://{domain}zoom.us/",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/74.0.3729.169 "
                       "Safari/537.36")
    }

    async with session.get(url, headers=agent_header) as response:
        html = await response.text()

    if password is not None:
        meet_id_regex = re.compile("<input[^>]*")
        for inp in meet_id_regex.findall(html):
            input_split = inp.split()
            if input_split[2] == 'id="meetId"':
                meet_id = input_split[3][7:-1]
                break

        data = {"id": meet_id,
                "passwd": password,
                "action": "viewdetailpage"}

        check_url = f"https://{domain}zoom.us/rec/validate_meet_passwd"
        async with session.post(check_url, data=data, headers=agent_header) as response:
            pass

        async with session.get(url, headers=agent_header) as response:
            html = await response.text()

    metadata = _get_page_meta(html, ("viewMp4Url", "topic"))
    if metadata is None:
        return None

    vid_url = metadata.get("viewMp4Url")
    extension = vid_url.split("?")[0].split("/")[-1].split(".")[1]
    name = file_name or metadata.get("topic")

    # We need to disable the decoding of the url, because zoom is not RFC-compliant (btw fuck zoom).
    await queue.put({
        "url": URL(vid_url, encoded=True),
        "path": safe_path_join(base_path, f"{name}.{extension}"),
        "session_kwargs": dict(headers=agent_header),
    })
