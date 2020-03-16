import video_portal
from custom import analysis, informatik
from downloader import *

import asyncio


async def main():
    if not settings.check_if_set():
        raise ValueError("Please run 'python setup.py'")

    queue = asyncio.Queue()

    async with aiohttp.ClientSession(raise_for_status=True) as session:
        nus2 = moodle_producer(session, queue, 11838)
        physik1 = moodle_producer(session, queue, 12228)
        koma1 = moodle_producer(session, queue, 12301)
        analysis2_moodle = moodle_producer(session, queue, 12611)
        analysis2 = custom_producer(analysis.parse_main_page, session, queue)
        informatik1 = custom_producer(informatik.parse_main_page, session, queue)

        if settings.use_video_portal:

            v_nus_2020 = video_portal.producer(session, queue, "d-itet", "2020", "spring", "227-0002-00L",
                                          pwd_username="bie-20s", pwd_password=settings.portal_nus2_2020_password)
            v_nus_2019 = video_portal.producer(session, queue, "d-itet", "2019", "spring", "227-0002-00L",
                                          pwd_username="bie-19s", pwd_password=settings.portal_nus2_2019_password)
            v_inf = video_portal.producer(session, queue, "d-infk", "2020", "spring", "252-0848-00L",
                                          pwd_username="scw-20s", pwd_password=settings.portal_inf1_password)
            v_analysis = video_portal.producer(session, queue, "d-math", "2020", "spring", "401-0232-10L")
            v_koma = video_portal.producer(session, queue, "d-math", "2020", "spring", "401-0302-10L")

            producers_portal = [
                asyncio.create_task(v_nus_2020),
                asyncio.create_task(v_nus_2019),
                asyncio.create_task(v_inf),
                asyncio.create_task(v_analysis),
                asyncio.create_task(v_koma),
            ]
        else:
            producers_portal = []

        producers_no_login = [
            asyncio.create_task(analysis2),
            asyncio.create_task(informatik1),
        ]

        await moodle.login_async(session)

        producers = [
            asyncio.create_task(nus2),
            asyncio.create_task(physik1),
            asyncio.create_task(koma1),
            asyncio.create_task(analysis2_moodle),
            *producers_no_login,
            *producers_portal,
        ]

        consumers = [asyncio.create_task(download_files(session, queue))
                     for _ in range(20)]

        await asyncio.gather(*producers)

        await queue.join()

        for c in consumers:
            c.cancel()


if __name__ == '__main__':
    import time

    start_t = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print(f"finished in {time.time() - start_t} seconds")
