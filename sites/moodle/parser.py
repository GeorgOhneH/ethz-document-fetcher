import asyncio
import logging
import re
import os
import pprint
from mimetypes import guess_extension

from aiohttp.client_exceptions import ClientResponseError
from bs4 import BeautifulSoup, SoupStrainer

from core.constants import BEAUTIFUL_SOUP_PARSER
from core.downloader import is_extension_forbidden
from core.exceptions import ForbiddenError
from core.storage.cache import check_url_reference
from core.storage.utils import call_function_or_cache
from core.utils import safe_path_join, safe_path
from sites import polybox, one_drive
from sites.moodle import zoom
from .constants import AJAX_SERVICE_URL, MTYPE_DIRECTORY, MTYPE_FILE, MTYPE_EXTERNAL_LINK, MTYPE_ASSIGN

logger = logging.getLogger(__name__)


async def parse_main_page(session,
                          queue,
                          html,
                          base_path,
                          site_settings,
                          moodle_id,
                          process_external_links,
                          keep_section_order,
                          password_mapper):
    sesskey = re.search(b"""sesskey":"([^"]+)""", html)[1].decode("utf-8")
    async with session.post(AJAX_SERVICE_URL, json=get_update_payload(moodle_id),
                            params={"sesskey": sesskey}) as response:
        update_json = await response.json()

    last_updated_dict = parse_update_json(update_json)

    only_sections = SoupStrainer("li", id=re.compile("section-([0-9]+)"))
    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER, parse_only=only_sections)

    sections = soup.find_all("li", id=re.compile("section-([0-9]+)"), recursive=False)

    coroutines = [parse_sections(session=session,
                                 queue=queue,
                                 section=section,
                                 base_path=base_path,
                                 site_settings=site_settings,
                                 moodle_id=moodle_id,
                                 process_external_links=process_external_links,
                                 last_updated_dict=last_updated_dict,
                                 password_mapper=password_mapper,
                                 index=index,
                                 keep_section_order=keep_section_order)
                  for index, section in enumerate(sections)]
    await asyncio.gather(*coroutines)


async def parse_sections(session,
                         queue,
                         section,
                         base_path,
                         site_settings,
                         moodle_id,
                         process_external_links,
                         last_updated_dict,
                         password_mapper,
                         index=None,
                         keep_section_order=False):
    section_name = str(section["aria-label"])
    if keep_section_order:
        section_name = f"[{index + 1:02}] {section_name}"
    base_path = safe_path_join(base_path, section_name)

    modules = section.find_all("li", id=re.compile("module-[0-9]+"))
    tasks = []
    for module in modules:
        coroutine = parse_mtype(session=session,
                                queue=queue,
                                site_settings=site_settings,
                                base_path=base_path,
                                module=module,
                                last_updated_dict=last_updated_dict,
                                moodle_id=moodle_id,
                                process_external_links=process_external_links,
                                password_mapper=password_mapper)

        tasks.append(asyncio.ensure_future(coroutine))

        if process_external_links:
            for text_link in module.find_all("a"):
                url = text_link.get("href", None)
                name = text_link.string
                if url is None or name is None:
                    continue

                coroutine = process_link(session=session,
                                         queue=queue,
                                         base_path=base_path,
                                         site_settings=site_settings,
                                         url=url,
                                         moodle_id=moodle_id,
                                         name=str(name),
                                         password_mapper=password_mapper)

                tasks.append(asyncio.ensure_future(exception_handler(coroutine, moodle_id, url)))

    await asyncio.gather(*tasks)


async def parse_mtype(session,
                      queue,
                      site_settings,
                      base_path,
                      module,
                      last_updated_dict,
                      moodle_id,
                      process_external_links,
                      password_mapper):
    mtype = module["class"][1]
    module_id = int(re.search("module-([0-9]+)", module["id"])[1])
    if mtype == MTYPE_FILE:
        instance = module.find("div", class_="activityinstance")
        try:
            file_name = str(instance.a.span.contents[0])
        except AttributeError:
            return
        last_updated = last_updated_dict[module_id]

        with_extension = False
        if "pdf-24" in instance.a.img["src"]:
            file_name += ".pdf"
            with_extension = True

        url = instance.a["href"] + "&redirect=1"
        await queue.put({"path": safe_path_join(base_path, file_name),
                         "url": url,
                         "with_extension": with_extension,
                         "checksum": last_updated})

    elif mtype == MTYPE_DIRECTORY:
        last_updated = last_updated_dict[module_id]
        await parse_folder(session, queue, site_settings, module, base_path, last_updated)

    elif mtype == MTYPE_EXTERNAL_LINK:
        if not process_external_links:
            return

        instance = module.find("div", class_="activityinstance")
        url = instance.a["href"] + "&redirect=1"
        name = str(instance.a.span.contents[0])

        driver_url = await check_url_reference(session, url)

        await process_link(session=session,
                           queue=queue,
                           base_path=base_path,
                           site_settings=site_settings,
                           url=driver_url,
                           moodle_id=moodle_id,
                           name=name,
                           password_mapper=password_mapper)

    elif mtype == MTYPE_ASSIGN:
        instance = module.find("div", class_="activityinstance")
        link = instance.a
        if link is not None:
            href = instance.a["href"]
            last_updated = last_updated_dict[module_id]
            name = str(instance.a.span.contents[0])

            assign_file_tree_soup_soup = await call_function_or_cache(get_assign_files_tree,
                                                                      last_updated,
                                                                      session,
                                                                      href)

            await parse_assign_files_tree(queue=queue,
                                          soup=assign_file_tree_soup_soup,
                                          path=safe_path_join(base_path, name))


async def get_filemanager(session, href):
    async with session.get(href) as response:
        text = await response.text()

    only_file_tree = SoupStrainer("div", id=re.compile("folder_tree[0-9]+"), class_="filemanager")
    return BeautifulSoup(text, BEAUTIFUL_SOUP_PARSER, parse_only=only_file_tree)


async def get_assign_files_tree(session, href):
    async with session.get(href) as response:
        text = await response.text()

    assign_files_tree = SoupStrainer("div", id=re.compile("assign_files_tree[0-9a-f]*"))
    return BeautifulSoup(text, BEAUTIFUL_SOUP_PARSER, parse_only=assign_files_tree)


async def parse_folder(session, queue, site_settings, module, base_path, last_updated):
    folder_tree = module.find("div", id=re.compile("folder_tree[0-9]+"), class_="filemanager")
    if folder_tree is not None:
        await parse_folder_tree(queue, folder_tree.ul, base_path, last_updated)
        return

    instance = module.find("div", class_="activityinstance")
    folder_name = str(instance.a.span.contents[0])
    folder_path = safe_path_join(base_path, folder_name)

    href = instance.a["href"]

    folder_soup = await call_function_or_cache(get_filemanager, last_updated, session, href)

    await parse_sub_folders(queue, folder_soup, folder_path, last_updated)


async def parse_sub_folders(queue, soup, folder_path, last_updated):
    folder_trees = soup.find_all("div", id=re.compile("folder_tree[0-9]+"), class_="filemanager")
    for folder_tree in folder_trees:
        await parse_folder_tree(queue, folder_tree.ul, folder_path, last_updated)


async def parse_folder_tree(queue, soup, folder_path, last_updated):
    children = soup.find_all("li", recursive=False)
    for child in children:
        if child.find("div", recursive=False) is not None:
            sub_folder_path = safe_path_join(folder_path, child.div.span.img["alt"])
        else:
            sub_folder_path = folder_path

        if child.find("ul", recursive=False) is not None:
            await parse_folder_tree(queue, child.ul, sub_folder_path, last_updated)

        if child.find("span", recursive=False) is not None:
            url = child.span.a["href"]
            name = child.span.a.find("span", recursive=False, class_="fp-filename").get_text(strip=True)
            item = {"path": safe_path_join(sub_folder_path, name), "url": url, "checksum": last_updated}
            await queue.put(item)


async def parse_assign_files_tree(queue, soup, path):
    for assign_files_tree in soup.find_all("div", id=re.compile("assign_files_tree[0-9a-f]*")):
        for item in assign_files_tree.ul.find_all("li", recursive=False):
            date_time = str(item.find("div", class_="fileuploadsubmissiontime").string)
            fileuploadsubmission_soup = item.find("div", class_="fileuploadsubmission")
            name = str(fileuploadsubmission_soup.a.string)
            url = fileuploadsubmission_soup.a["href"]

            await queue.put({
                "path": safe_path_join(path, name),
                "url": url,
                "checksum": date_time,
            })


async def exception_handler(coroutine, moodle_id, url):
    try:
        await coroutine
    except asyncio.CancelledError:
        raise asyncio.CancelledError()
    except Exception as e:
        logger.error(f"Got an unexpected error from moodle: {moodle_id} "
                     f"while trying to access {url}, Error: {type(e).__name__}: {e}", exc_info=True)


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
        raise ForbiddenError(update_json[0]["exception"]["errorcode"] + ", " + update_json[0]["exception"]["message"])

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


async def process_link(session, queue, base_path, site_settings, url, moodle_id, name, password_mapper):
    if "onedrive.live.com" in url:
        logger.debug(f"Starting one drive from moodle: {moodle_id}")
        await one_drive.producer(session,
                                 queue,
                                 base_path + f"; {safe_path(name)}",
                                 site_settings=site_settings,
                                 url=url)

    elif "polybox" in url:
        logger.debug(f"Starting polybox from moodle: {moodle_id}")
        poly_type, poly_id = [x.strip() for x in url.split("/") if x.strip() != ""][3:5]
        password = match_name_to_password(name, password_mapper)
        await polybox.producer(session,
                               queue,
                               safe_path_join(base_path, name),
                               site_settings,
                               poly_id,
                               poly_type=poly_type,
                               password=password)

    elif "zoom.us/rec/play" in url or "zoom.us/rec/share" in url:
        if is_extension_forbidden("mp4",
                                  site_settings.allowed_extensions + queue.consumer_kwargs["allowed_extensions"],
                                  site_settings.forbidden_extensions + queue.consumer_kwargs["forbidden_extensions"]):
            logger.debug(f"Skipped zoom download from moodle: {moodle_id}")
            return
        logger.debug(f"Starting zoom download from moodle: {moodle_id}")
        password = match_name_to_password(name, password_mapper)
        await zoom.download(session=session,
                            queue=queue,
                            base_path=base_path,
                            url=url,
                            file_name=name,
                            password=password)


def match_name_to_password(name, password_mapper):
    if password_mapper:
        for map_obj in password_mapper:
            if re.search(map_obj["name"], name):
                return map_obj["password"]
    return None
