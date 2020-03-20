from utils import safe_path_join
from video_portal.constants import *
from video_portal.login import login


async def producer(session, queue, department, year, semester, course_id, pwd_username=None, pwd_password=None):
    course_url = f"{BASE_URL}{department}/{year}/{semester}/{course_id}"

    meta_url = course_url + ".series-metadata.json"

    async with session.get(meta_url) as response:
        meta_data = await response.json()

    course_name = meta_data["title"]

    base_path = safe_path_join(settings.video_portal_path, course_name)

    downloaded_episodes = os.listdir(base_path)

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

        meta_video_data = await login(session, department, year, semester, course_id,
                                      meta_video_url, pwd_username, pwd_password)

        url = meta_video_data["selectedEpisode"]["media"]["presentations"][0]["url"]
        await queue.put({"path": safe_path_join(base_path, file_name), "url": url})
