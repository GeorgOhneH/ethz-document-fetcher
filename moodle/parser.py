import asyncio
import re

import one_drive
import polybox
from constants import *
from utils import *
from .constants import *


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
            img = instance.a.img["src"]
        except AttributeError:
            continue

        if img == PDF_IMG:
            file_name = str(instance.a.span.contents[0]) + ".pdf"
            url = instance.a["href"] + "&redirect=1"
            await queue.put({"path": safe_path_join(base_path, file_name), "url": url})

        elif img == FOLDER_IMG:
            await parse_folder(session, queue, instance, base_path)

        elif img == EXTERNAL_LINK_IMG:
            url = instance.a["href"] + "&redirect=1"
            name = str(instance.a.span.contents[0])

            url_reference_path = os.path.join(CACHE_PATH, "url.json")
            driver_url = await check_url_reference(session, url, url_reference_path)

            if "onedrive.live.com" in driver_url:
                await one_drive.producer(session, queue, driver_url, base_path + f"; {make_string_path_safe(name)}")

            elif "polybox" in driver_url:
                poly_id = driver_url.split("/")[-1]
                await polybox.producer(queue, poly_id, safe_path_join(base_path, name))

    await parse_sub_folders(queue, soup=section, folder_path=base_path)


async def parse_folder(session, queue, instance, base_path):
    folder_name = str(instance.a.span.contents[0])
    href = instance.a["href"]

    async with session.get(href) as response:
        text = await response.text()

    folder_soup = BeautifulSoup(text, BEAUTIFUL_SOUP_PARSER)
    folder_path = safe_path_join(base_path, folder_name)
    await parse_sub_folders(queue, soup=folder_soup, folder_path=folder_path)


async def parse_sub_folders(queue, soup, folder_path, use_sub_folder_name=True):
    sub_folders = remove_duplicated(set(filter(test_for_sub_folder, soup.find_all("span", class_="fp-filename"))))
    for sub_folder in sub_folders:
        sub_folder_name = str(sub_folder.string)
        sub_folder_content = sub_folder.parent.next_sibling
        if sub_folder_content is None:
            continue

        sub_files_or_sub_sub_folders = sub_folder_content.find_all("span", class_="fp-filename")
        if sub_files_or_sub_sub_folders is None:
            continue

        sub_files = filter(test_for_not_sub_folder, sub_files_or_sub_sub_folders)

        if sub_folder_name not in ["None"]:
            sub_folder_path = safe_path_join(folder_path, sub_folder_name)
        else:
            sub_folder_path = folder_path

        for sub_file in sub_files:
            sub_file_name = str(sub_file.string)
            sub_url = sub_file.parent.get("href", None)
            if sub_url is not None:
                await queue.put({"path": safe_path_join(sub_folder_path, sub_file_name), "url": sub_url})


def remove_duplicated(tags):
    to_be_removed = set([])
    for tag in tags:
        sub_folder_content = tag.parent.next_sibling
        if sub_folder_content is None:
            to_be_removed.add(tag)
            continue
        sub_sub_folders = filter(test_for_sub_folder, sub_folder_content.find_all("span", class_="fp-filename"))
        if any([(x in tags) for x in sub_sub_folders]):
            to_be_removed.add(tag)

    return tags - to_be_removed


def test_for_sub_folder(tag):
    return tag.previous_sibling.img["src"] == SUB_FOLDER_IMG


def test_for_not_sub_folder(tag):
    return tag.previous_sibling.img["src"] != SUB_FOLDER_IMG
