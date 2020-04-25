import asyncio
import logging
import copy
import re

from aiohttp.client_exceptions import ClientResponseError

import one_drive
import polybox
from constants import *
from utils import *
from .constants import *

logger = logging.getLogger(__name__)


async def parse_main_page(session, queue, html):
    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

    header = soup.find("div", class_="page-header-headings")
    header_name = str(header.h1.string)

    sections = soup.find_all("li", id=re.compile("section-([0-9]+)"))

    coroutines = [parse_sections(session, queue, section, header_name) for section in sections]
    await asyncio.gather(*coroutines)


async def parse_sections(session, queue, section, header_name):
    section_name = str(section["aria-label"])
    base_path = safe_path_join(header_name, section_name)

    instances = section.find_all("div", class_="activityinstance")

    for instance in reversed(instances):

        try:
            mtype = str(instance.a.span.span.string).strip()
        except AttributeError:
            continue

        if mtype == MTYPE_FILE:
            file_name = str(instance.a.span.contents[0])
            url = instance.a["href"] + "&redirect=1"
            await queue.put({"path": safe_path_join(base_path, file_name), "url": url, "extension": False})

        elif mtype == MTYPE_DIRECTORY:
            await parse_folder(session, queue, instance, base_path)

        elif mtype == MTYPE_EXTERNAL_LINK:
            url = instance.a["href"] + "&redirect=1"
            name = str(instance.a.span.contents[0])

            url_reference_path = os.path.join(CACHE_PATH, "url.json")
            driver_url = await check_url_reference(session, url, url_reference_path)

            if "onedrive.live.com" in driver_url:
                await one_drive.producer(session, queue, driver_url, base_path + f"; {safe_path(name)}")

            elif "polybox" in driver_url:
                poly_id = driver_url.split("s/")[-1].split("/")[0]
                try:
                    await polybox.producer(queue, poly_id, safe_path_join(base_path, name))
                except ClientResponseError:
                    logger.warning(f"Couldn't access polybox with id: {poly_id} from moodle: {header_name}")

    await parse_sub_folders(queue, soup=section, folder_path=base_path)


async def parse_folder(session, queue, instance, base_path):
    folder_name = str(instance.a.span.contents[0])
    href = instance.a["href"]

    async with session.get(href) as response:
        text = await response.text()

    folder_soup = BeautifulSoup(text, BEAUTIFUL_SOUP_PARSER)
    folder_path = safe_path_join(base_path, folder_name)
    await parse_sub_folders(queue, soup=folder_soup, folder_path=folder_path)


async def parse_sub_folders(queue, soup, folder_path):
    folder_trees = soup.find_all("div", id=re.compile("folder_tree[0-9]+"), class_="filemanager")
    for folder_tree in folder_trees:
        await parse_folder_tree(queue, folder_tree.ul, folder_path)


async def parse_folder_tree(queue, soup, folder_path):
    children = soup.find_all("li", recursive=False)
    for child in children:
        if child.find("div", recursive=False) is not None:
            sub_folder_path = safe_path_join(folder_path, child.div.span.img["alt"])
        else:
            sub_folder_path = folder_path

        if child.find("ul", recursive=False) is not None:
            await parse_folder_tree(queue, child.ul, sub_folder_path)

        if child.find("span", recursive=False) is not None:
            url = child.span.a["href"]
            name = child.span.a.find("span", recursive=False, class_="fp-filename").get_text(strip=True)
            await queue.put({"path": safe_path_join(sub_folder_path, name), "url": url})
