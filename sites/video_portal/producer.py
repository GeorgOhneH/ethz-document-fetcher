import asyncio
import os

from core.utils import safe_path_join
from settings.config import ConfigString
from sites.video_portal.constants import BASE_URL

DEPARTMENT_CONFIG = ConfigString(gui_name="Department")
YEAR_CONFIG = ConfigString(gui_name="Year")
SEMESTER_CONFIG = ConfigString(gui_name="Semester")
COURSE_ID_CONFIG = ConfigString(gui_name="Course ID")
PWD_USERNAME_CONFIG = ConfigString(gui_name="Series Username", optional=True)
PWD_PASSWORD_CONFIG = ConfigString(gui_name="Series Password", optional=True)


async def get_meta_data(session, course_url):
    meta_url = course_url + ".series-metadata.json"
    async with session.get(meta_url) as response:
        meta_data = await response.json()

    return meta_data


async def get_folder_name(session, department, year, semester, course_id, **kwargs):
    course_url = f"{BASE_URL}{department}/{year}/{semester}/{course_id}"

    meta_data = await get_meta_data(session, course_url)

    return meta_data["title"]


async def producer(session,
                   queue,
                   base_path,
                   download_settings,
                   department: DEPARTMENT_CONFIG,
                   year: YEAR_CONFIG,
                   semester: SEMESTER_CONFIG,
                   course_id: COURSE_ID_CONFIG,
                   pwd_username: PWD_USERNAME_CONFIG = None,
                   pwd_password: PWD_PASSWORD_CONFIG = None):
    absolute_path = os.path.join(download_settings.save_path, base_path)
    course_url = f"{BASE_URL}{department}/{year}/{semester}/{course_id}"

    meta_data = await get_meta_data(session, course_url)

    if os.path.exists(absolute_path):
        downloaded_episodes = os.listdir(absolute_path)
    else:
        downloaded_episodes = []

    tasks = []
    for episode in meta_data["episodes"]:
        ep_id = episode['id']
        name = episode["title"]
        date_time = episode["createdAt"]

        date, time = date_time.split("T")

        file_name = f"{date} {name}.mp4"
        if file_name in downloaded_episodes:
            continue

        video_url = f"{course_url}/{ep_id}"

        meta_video_url = video_url + ".series-metadata.json"

        coroutine = put_in_queue(session,
                                 queue,
                                 safe_path_join(base_path, file_name),
                                 download_settings,
                                 department,
                                 year,
                                 semester,
                                 course_id,
                                 meta_video_url,
                                 pwd_username,
                                 pwd_password)

        tasks.append(asyncio.ensure_future(coroutine))

    await asyncio.gather(*tasks)


async def put_in_queue(session,
                       queue,
                       base_path,
                       download_settings,
                       department,
                       year,
                       semester,
                       course_id,
                       meta_video_url,
                       pwd_username,
                       pwd_password):
    meta_video_data = await login_and_data(session, download_settings, department, year, semester, course_id,
                                           meta_video_url, pwd_username, pwd_password)

    url = meta_video_data["selectedEpisode"]["media"]["presentations"][0]["url"]
    await queue.put({"path": base_path, "url": url})


async def login_and_data(session, download_settings, department, year, semester, course_id, meta_video_url,
                         pwd_username=None, pwd_password=None, depth=0):
    course_url = f"{BASE_URL}{department}/{year}/{semester}/{course_id}"

    async with session.get(meta_video_url) as response:
        meta_data = await response.json()

    if meta_data["authorized"]:
        return meta_data

    if depth >= 4:
        raise Exception("could not log in after 4 tries")

    protection = meta_data["protection"]

    if protection == "ETH":
        security_check_url = f"{BASE_URL}{department}/{year}/{semester}/j_security_check"
        async with session.post(security_check_url, data=get_eth_auth(download_settings)) as response:
            await response.text()

    elif protection == "PWD":
        if not pwd_username or not pwd_username:
            raise ValueError("pwd_username and pwd_password must be set")
        pwd_data = {
            "_charset_": "utf-8",
            "username": pwd_username,
            "password": pwd_password,
        }
        series_url = course_url + ".series-login.json"
        async with session.post(series_url, data=pwd_data) as response:
            await response.text()

    return await login_and_data(session,
                                download_settings,
                                department,
                                year,
                                semester,
                                course_id,
                                meta_video_url,
                                pwd_username=pwd_username,
                                pwd_password=pwd_password,
                                depth=depth + 1)


def get_eth_auth(download_settings):
    return {
        "_charset_": "utf-8",
        "j_username": download_settings.username,
        "j_password": download_settings.password,
        "j_validate": "true",
    }
