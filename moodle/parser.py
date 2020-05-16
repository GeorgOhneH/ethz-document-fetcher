import asyncio
import traceback

from aiohttp.client_exceptions import ClientResponseError
from bs4 import BeautifulSoup, SoupStrainer

import one_drive
import polybox
from core.constants import BEAUTIFUL_SOUP_PARSER
from core.utils import *
from settings import settings
from .constants import *

logger = logging.getLogger(__name__)


async def parse_main_page(session, queue, html, base_path, moodle_id, use_external_links):
    sesskey = re.search(b"""sesskey":"([^"]+)""", html)[1].decode("utf-8")
    async with session.post(AJAX_SERVICE_URL, json=get_update_payload(moodle_id),
                            params={"sesskey": sesskey}) as response:
        update_json = await response.json()

    last_updated_dict = parse_update_json(update_json)

    only_sections = SoupStrainer("li", id=re.compile("section-([0-9]+)"))
    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER, parse_only=only_sections)

    sections = soup.find_all("li", id=re.compile("section-([0-9]+)"), recursive=False)

    coroutines = [parse_sections(session, queue, section, base_path, moodle_id, use_external_links, last_updated_dict)
                  for section in sections]
    await asyncio.gather(*coroutines)


async def parse_sections(session, queue, section, base_path, moodle_id, use_external_links, last_updated_dict):
    section_name = str(section["aria-label"])
    base_path = safe_path_join(base_path, section_name)

    modules = section.find_all("li", id=re.compile("module-[0-9]+"))
    tasks = []
    for module in modules:
        mtype = module["class"][1]
        module_id = int(re.search("module-([0-9]+)", module["id"])[1])

        if mtype == MTYPE_FILE:
            instance = module.find("div", class_="activityinstance")
            try:
                file_name = str(instance.a.span.contents[0])
            except AttributeError:
                continue
            last_updated = last_updated_dict[module_id]

            with_extension = False
            if instance.a.img["src"] == PDF_IMAGE:
                file_name += ".pdf"
                with_extension = True

            url = instance.a["href"] + "&redirect=1"
            await queue.put({"path": safe_path_join(base_path, file_name), "url": url,
                             "with_extension": with_extension, "checksum": last_updated})

        elif mtype == MTYPE_DIRECTORY:
            last_updated = last_updated_dict[module_id]
            coroutine = parse_folder(session, queue, module, base_path, last_updated)
            tasks.append(asyncio.create_task(coroutine))

        elif mtype == MTYPE_EXTERNAL_LINK:
            if not use_external_links:
                continue

            instance = module.find("div", class_="activityinstance")
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

    await asyncio.gather(*tasks)


async def parse_folder(session, queue, module, base_path, last_updated):
    folder_tree = module.find("div", id=re.compile("folder_tree[0-9]+"), class_="filemanager")
    if folder_tree is not None:
        await parse_folder_tree(queue, folder_tree.ul, base_path, last_updated)
        return

    instance = module.find("div", class_="activityinstance")
    folder_name = str(instance.a.span.contents[0])
    folder_path = safe_path_join(base_path, folder_name)

    cache_key = folder_path + "last_updated"
    last_updated_cache = get_element_from_cache(cache_key)

    cache_items_key = folder_path + "item_key"
    if last_updated == last_updated_cache:
        items = get_element_from_cache(cache_items_key)
        if items is not None:
            for item in items:
                await queue.put(item)
            return

    href = instance.a["href"]
    async with session.get(href) as response:
        text = await response.text()

    only_file_tree = SoupStrainer("div", id=re.compile("folder_tree[0-9]+"), class_="filemanager")
    folder_soup = BeautifulSoup(text, BEAUTIFUL_SOUP_PARSER, parse_only=only_file_tree)
    cache_items = []
    await parse_sub_folders(queue, folder_soup, folder_path, last_updated, cache_items)
    save_element_to_cache(cache_items_key, cache_items)
    save_element_to_cache(cache_key, last_updated)


async def parse_sub_folders(queue, soup, folder_path, last_updated, cache_items=None):
    folder_trees = soup.find_all("div", id=re.compile("folder_tree[0-9]+"), class_="filemanager")
    for folder_tree in folder_trees:
        await parse_folder_tree(queue, folder_tree.ul, folder_path, last_updated, cache_items)


async def parse_folder_tree(queue, soup, folder_path, last_updated, cache_items=None):
    children = soup.find_all("li", recursive=False)
    for child in children:
        if child.find("div", recursive=False) is not None:
            sub_folder_path = safe_path_join(folder_path, child.div.span.img["alt"])
        else:
            sub_folder_path = folder_path

        if child.find("ul", recursive=False) is not None:
            await parse_folder_tree(queue, child.ul, sub_folder_path, last_updated, cache_items)

        if child.find("span", recursive=False) is not None:
            url = child.span.a["href"]
            name = child.span.a.find("span", recursive=False, class_="fp-filename").get_text(strip=True)
            item = {"path": safe_path_join(sub_folder_path, name), "url": url, "checksum": last_updated}
            await queue.put(item)
            if cache_items is not None:
                cache_items.append(item)


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


def get_update_payload(courseid, since=0):
    return [{
        "index": 0,
        "methodname": "core_course_get_updates_since",
        "args": {
            "courseid": courseid,
            "since": since,
        }
    }]


def parse_update_json(update_json):
    if update_json[0]["error"]:
        raise ValueError("update json has an error")

    result = {}
    for instance in update_json[0]["data"]["instances"]:
        if instance["contextlevel"] != "module":
            continue

        instance_id = instance["id"]
        last_update = None
        for update in instance["updates"]:
            if update["name"] == "configuration":
                last_update = update["timeupdated"]
                break

        if last_update is None:
            raise ValueError(f"Did not found a timeupdated field in {instance['updates']}")

        result[instance_id] = last_update

    return result
