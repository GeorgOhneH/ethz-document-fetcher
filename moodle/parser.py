import asyncio
import traceback

from aiohttp.client_exceptions import ClientResponseError
from bs4 import BeautifulSoup, SoupStrainer

import one_drive
import polybox
from core.constants import BEAUTIFUL_SOUP_PARSER
from core.utils import *
from settings import settings
from .constants import MTYPE_EXTERNAL_LINK, MTYPE_DIRECTORY, MTYPE_FILE, PDF_IMAGE

logger = logging.getLogger(__name__)


async def parse_main_page(session, queue, html, base_path, moodle_id, use_external_links):
    only_sections = SoupStrainer("li", id=re.compile("section-([0-9]+)"))
    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER, parse_only=only_sections)

    sections = soup.find_all("li", id=re.compile("section-([0-9]+)"), recursive=False)

    coroutines = [parse_sections(session, queue, section, base_path, moodle_id, use_external_links)
                  for section in sections]
    await asyncio.gather(*coroutines)


async def parse_sections(session, queue, section, base_path, moodle_id, use_external_links):
    section_name = str(section["aria-label"])
    base_path = safe_path_join(base_path, section_name)

    instances = section.find_all("div", class_="activityinstance")

    tasks = []
    for instance in reversed(instances):
        try:
            instance.a.span
        except AttributeError:
            continue

        mtype = instance.parent.parent.parent.parent["class"][1]

        if mtype == MTYPE_FILE:
            file_name = str(instance.a.span.contents[0])
            extension = False
            if instance.a.img["src"] == PDF_IMAGE:
                file_name += ".pdf"
                extension = True

            url = instance.a["href"] + "&redirect=1"
            await queue.put({"path": safe_path_join(base_path, file_name), "url": url, "extension": extension})

        elif mtype == MTYPE_DIRECTORY:
            coroutine = parse_folder(session, queue, instance, base_path)
            tasks.append(asyncio.create_task(coroutine))

        elif mtype == MTYPE_EXTERNAL_LINK:
            if not use_external_links:
                continue

            url = instance.a["href"] + "&redirect=1"
            name = str(instance.a.span.contents[0])

            driver_url = await check_url_reference(session, url)

            coroutine = None
            if "onedrive.live.com" in driver_url:
                logger.debug(f"Starting one drive from moodle: {moodle_id}")
                coroutine = one_drive.producer(session, queue, base_path + f"; {safe_path(name)}", driver_url)

            elif "polybox" in driver_url:
                logger.debug(f"Starting polybox from moodle: {moodle_id}")
                poly_id = driver_url.split("s/")[-1].split("/")[0]
                coroutine = poly_box_wrapper(polybox.producer, moodle_id)(session, queue, poly_id,
                                                                          safe_path_join(base_path, name))

            if coroutine is not None:
                tasks.append(asyncio.create_task(exception_handler(coroutine, moodle_id, driver_url)))

    await asyncio.gather(parse_sub_folders(queue, soup=section, folder_path=base_path), *tasks)


async def parse_folder(session, queue, instance, base_path):
    folder_name = str(instance.a.span.contents[0])
    href = instance.a["href"]

    async with session.get(href) as response:
        text = await response.text()

    await asyncio.sleep(0)
    only_file_tree = SoupStrainer("div", id=re.compile("folder_tree[0-9]+"), class_="filemanager")
    folder_soup = BeautifulSoup(text, BEAUTIFUL_SOUP_PARSER, parse_only=only_file_tree)
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


def poly_box_wrapper(func, moodle_id):
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except ClientResponseError:
            if "id" in kwargs:
                poly_id = kwargs["id"]
            else:
                poly_id = args[2]
            logger.warning(f"Couldn't access polybox with id: {poly_id} from moodle: {moodle_id}")
    return wrapper


async def exception_handler(coroutine, moodle_id, url):
    try:
        await coroutine
    except asyncio.CancelledError:
        raise asyncio.CancelledError()
    except Exception as e:
        if settings.loglevel == "DEBUG":
            traceback.print_exc()
        logger.error(f"Got an unexpected error from moodle: {moodle_id} "
                     f"while trying to access {url}, Error: {type(e).__name__}: {e}")
