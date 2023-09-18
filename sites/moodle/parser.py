import asyncio
import logging
import re

import aiohttp
from bs4 import BeautifulSoup, SoupStrainer

from core.exceptions import ForbiddenError
from core.storage import cache
from core.storage.cache import check_url_reference
from core.storage.utils import call_function_or_cache
from core.utils import safe_path_join, get_beautiful_soup_parser, add_extension
from sites.exceptions import NotSingleFile
from sites.utils import process_single_file_url
from .constants import AJAX_SERVICE_URL, MTYPE_DIRECTORY, MTYPE_FILE, MTYPE_EXTERNAL_LINK, MTYPE_ASSIGN, MTYPE_LABEL

logger = logging.getLogger(__name__)


async def parse_main_page(session,
                          queue,
                          html,
                          base_path,
                          download_settings,
                          moodle_id,
                          process_external_links,
                          keep_section_order,
                          keep_file_order,
                          password_mapper):
    sesskey = re.search(b"""sesskey":"([^"]+)""", html)[1].decode("utf-8")

    update_json = await get_update_json(session=session,
                                        moodle_id=moodle_id,
                                        sesskey=sesskey)

    last_updated_dict = parse_update_json(update_json)

    only_sections = SoupStrainer("li", id=re.compile("section-([0-9]+)"))
    soup = BeautifulSoup(html, get_beautiful_soup_parser(), parse_only=only_sections)

    sections = soup.find_all("li", id=re.compile("section-([0-9]+)"), recursive=False)

    coroutines = [parse_sections(session=session,
                                 queue=queue,
                                 section=section,
                                 base_path=base_path,
                                 download_settings=download_settings,
                                 moodle_id=moodle_id,
                                 process_external_links=process_external_links,
                                 last_updated_dict=last_updated_dict,
                                 password_mapper=password_mapper,
                                 index=index,
                                 keep_section_order=keep_section_order,
                                 keep_file_order=keep_file_order)
                  for index, section in enumerate(sections)]
    await asyncio.gather(*coroutines)


async def parse_sections(session,
                         queue,
                         section,
                         base_path,
                         download_settings,
                         moodle_id,
                         process_external_links,
                         last_updated_dict,
                         password_mapper,
                         index=None,
                         keep_section_order=False,
                         keep_file_order=False):

    title = section.find("h3", id=re.compile("sectionid-([0-9]+)-title"), recursive=True)
    section_name = str(title.text).strip()

    if keep_section_order:
        section_name = f"[{index + 1:02}] {section_name}"
    base_path = safe_path_join(base_path, section_name)

    title_link = section.find("a", href=re.compile(r"id=[0-9]+&section=[0-9]+"))
    if title_link is not None:
        # Old moodle site where we have to call the section explicit with a request
        await parse_single_section(session=session,
                                   queue=queue,
                                   download_settings=download_settings,
                                   base_path=base_path,
                                   href=title_link["href"],
                                   moodle_id=moodle_id,
                                   last_updated_dict=last_updated_dict,
                                   process_external_links=process_external_links,
                                   keep_file_order=keep_file_order,
                                   password_mapper=password_mapper)

    await _parse_section(session=session,
                         queue=queue,
                         download_settings=download_settings,
                         base_path=base_path,
                         section=section,
                         last_updated_dict=last_updated_dict,
                         moodle_id=moodle_id,
                         process_external_links=process_external_links,
                         keep_file_order=keep_file_order,
                         password_mapper=password_mapper)


async def parse_single_section(session,
                               queue,
                               download_settings,
                               base_path,
                               href,
                               moodle_id,
                               last_updated_dict,
                               process_external_links,
                               keep_file_order,
                               password_mapper):
    async with session.get(href) as response:
        html = await response.read()

    section_id = re.search(r"&section=([0-9]+)", href).group(1)

    only_sections = SoupStrainer("li", id=f"section-{section_id}")
    soup = BeautifulSoup(html, get_beautiful_soup_parser(), parse_only=only_sections)
    section = soup.find("li", id=f"section-{section_id}")

    await _parse_section(session=session,
                         queue=queue,
                         download_settings=download_settings,
                         base_path=base_path,
                         section=section,
                         last_updated_dict=last_updated_dict,
                         moodle_id=moodle_id,
                         process_external_links=process_external_links,
                         keep_file_order=keep_file_order,
                         password_mapper=password_mapper)


async def _parse_section(session,
                         queue,
                         download_settings,
                         base_path,
                         section,
                         last_updated_dict,
                         moodle_id,
                         process_external_links,
                         keep_file_order,
                         password_mapper):
    modules = section.find_all("li", id=re.compile("module-[0-9]+"))
    tasks = []
    for idx, module in enumerate(modules):
        coroutine = parse_module(session=session,
                                 queue=queue,
                                 download_settings=download_settings,
                                 base_path=base_path,
                                 module=module,
                                 module_idx=idx,
                                 last_updated_dict=last_updated_dict,
                                 moodle_id=moodle_id,
                                 process_external_links=process_external_links,
                                 keep_file_order=keep_file_order,
                                 password_mapper=password_mapper)
        tasks.append(coroutine)

    await asyncio.gather(*tasks)


async def parse_module(session,
                       queue,
                       download_settings,
                       base_path,
                       module,
                       module_idx,
                       last_updated_dict,
                       moodle_id,
                       process_external_links,
                       keep_file_order,
                       password_mapper):
    mtype = module["class"][2]
    module_id = int(re.search("module-([0-9]+)", module["id"])[1])
    if mtype == MTYPE_FILE:
        link = module.find("a")
        try:
            file_name = str(link.span.contents[0])
        except AttributeError:
            return
        last_updated = last_updated_dict[module_id]

        if keep_file_order:
            file_name = f"[{module_idx + 1:02}] {file_name}"

        url = link["href"] + "&redirect=1"
        await queue.put({"path": safe_path_join(base_path, file_name),
                         "url": url,
                         "with_extension": False,
                         "checksum": last_updated})

    elif mtype == MTYPE_DIRECTORY:
        last_updated = last_updated_dict[module_id]
        await parse_folder(session, queue, download_settings, module, base_path, last_updated)

    elif mtype == MTYPE_EXTERNAL_LINK:
        if not process_external_links:
            return

        link = module.find("a")
        url = link["href"] + "&redirect=1"
        name = str(link.span.contents[0])

        if keep_file_order:
            name = f"[{module_idx + 1:02}] {name}"

        driver_url = await check_url_reference(session, url)

        await process_link(session=session,
                           queue=queue,
                           base_path=base_path,
                           download_settings=download_settings,
                           url=driver_url,
                           moodle_id=moodle_id,
                           name=name,
                           password_mapper=password_mapper)

    elif mtype == MTYPE_ASSIGN:
        link = module.find("a")
        if link is None:
            return
        href = link["href"]
        last_updated = last_updated_dict[module_id]
        name = str(link.span.contents[0])

        assign_file_tree_soup_soup = await call_function_or_cache(get_assign_files_tree,
                                                                  last_updated,
                                                                  session,
                                                                  href)

        if keep_file_order:
            name = f"[{module_idx + 1:02}] {name}"

        await parse_assign_files_tree(queue=queue,
                                      soup=assign_file_tree_soup_soup,
                                      path=safe_path_join(base_path, name))
    elif mtype == MTYPE_LABEL:
        if not process_external_links:
            return

        for text_link in module.find_all("a"):
            url = text_link.get("href", None)
            name = text_link.text
            if url is None or not name:
                continue

            name = str(name)
            if keep_file_order:
                name = f"[{module_idx + 1:02}] {name}"

            await process_link(session=session,
                               queue=queue,
                               base_path=base_path,
                               download_settings=download_settings,
                               url=url,
                               moodle_id=moodle_id,
                               name=name,
                               password_mapper=password_mapper)


async def get_filemanager(session, href):
    async with session.get(href) as response:
        text = await response.text()

    only_file_tree = SoupStrainer("div", id=re.compile("folder_tree[0-9]+"), class_="filemanager")
    return BeautifulSoup(text, get_beautiful_soup_parser(), parse_only=only_file_tree)


async def get_assign_files_tree(session, href):
    async with session.get(href) as response:
        text = await response.text()

    assign_files_tree = SoupStrainer("div", id=re.compile("assign_files_tree[0-9a-f]*"))
    return BeautifulSoup(text, get_beautiful_soup_parser(), parse_only=assign_files_tree)


async def parse_folder(session, queue, download_settings, module, base_path, last_updated):
    folder_tree = module.find("div", id=re.compile("folder_tree[0-9]+"), class_="filemanager")
    if folder_tree is not None:
        await parse_folder_tree(queue, folder_tree.ul, base_path, last_updated)
        return

    link = module.find("a")
    folder_name = str(link.span.contents[0])
    folder_path = safe_path_join(base_path, folder_name)

    href = link["href"]

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


async def get_update_json(session, moodle_id, sesskey):
    async with session.post(AJAX_SERVICE_URL,
                            json=get_update_payload(moodle_id),
                            params={"sesskey": sesskey}) as response:
        return await response.json()


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


async def process_link(session, queue, base_path, download_settings, url, moodle_id, name, password_mapper):
    try:
        guess_extension = await cache.check_extension(session, url)
    except aiohttp.client_exceptions.ClientResponseError:
        return

    if guess_extension is None or guess_extension in ["html", "json"]:
        password = match_name_to_password(name, password_mapper)
        try:
            await process_single_file_url(session=session,
                                          queue=queue,
                                          base_path=base_path,
                                          download_settings=download_settings,
                                          url=url,
                                          name=name,
                                          password=password)
        except NotSingleFile:
            pass
    else:
        name = add_extension(name, guess_extension)
        await queue.put({
            "url": url,
            "path": safe_path_join(base_path, name)
        })


def match_name_to_password(name, password_mapper):
    if password_mapper:
        for map_obj in password_mapper:
            if re.search(map_obj["name"], name):
                return map_obj["password"]
    return None
