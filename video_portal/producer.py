from video_portal.login import login

from video_portal.constants import *


async def producer(session, queue, department, year, semester, course_id, pwd_username=None, pwd_password=None):
    course_url = f"{BASE_URL}{department}/{year}/{semester}/{course_id}"

    meta_data = await login(session, department, year, semester, course_id, pwd_username, pwd_password)

    course_name = meta_data["title"]

    base_path = os.path.join("video portal", course_name)

    for episode in meta_data["episodes"]:
        ep_id = episode['id']
        name = episode["title"]
        date = episode["createdAt"]

        date, time = date.split("T")

        file_name = f"{date} {name}.mp4"

        video_url = f"{course_url}/{ep_id}"

        meta_video_url = video_url + ".series-metadata.json"

        async with session.get(meta_video_url) as response:
            meta_video_data = await response.json()

        url = meta_video_data["selectedEpisode"]["media"]["presentations"][0]["url"]
        await queue.put({"path": os.path.join(base_path, file_name), "url": url})

