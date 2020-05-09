import asyncio

from core.utils import safe_path_join
from video_portal.constants import *
from video_portal.login import login_and_data


async def get_meta_data(session, course_url):
    meta_url = course_url + ".series-metadata.json"
    async with session.get(meta_url) as response:
        meta_data = await response.json()

    return meta_data


async def get_folder_name(session, department, year, semester, course_id, **kwargs):
    course_url = f"{BASE_URL}{department}/{year}/{semester}/{course_id}"

    meta_data = await get_meta_data(session, course_url)

    return meta_data["title"]


async def producer(session, queue, base_path, department, year, semester,
                   course_id, pwd_username=None, pwd_password=None):
    base_path = os.path.join(settings.base_path, base_path)
    course_url = f"{BASE_URL}{department}/{year}/{semester}/{course_id}"

    meta_data = await get_meta_data(session, course_url)

    if os.path.exists(base_path):
        downloaded_episodes = os.listdir(base_path)
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
                                 department,
                                 year,
                                 semester,
                                 course_id,
                                 meta_video_url,
                                 pwd_username,
                                 pwd_password)

        tasks.append(asyncio.create_task(coroutine))

    await asyncio.gather(*tasks)


async def put_in_queue(session,
                       queue,
                       base_path,
                       department,
                       year,
                       semester,
                       course_id,
                       meta_video_url,
                       pwd_username,
                       pwd_password):

    meta_video_data = await login_and_data(session, department, year, semester, course_id,
                                           meta_video_url, pwd_username, pwd_password)

    url = meta_video_data["selectedEpisode"]["media"]["presentations"][0]["url"]
    await queue.put({"path": base_path, "url": url})
