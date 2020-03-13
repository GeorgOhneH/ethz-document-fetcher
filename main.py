from settings import settings
import aiohttp
import asyncio

from custom import analysis, informatik
from downloader import *
import video_portal


async def main():
    queue = asyncio.Queue()

    async with aiohttp.ClientSession(raise_for_status=True) as session:
        nus2 = moodle_producer(session, queue, 11838)
        physik1 = moodle_producer(session, queue, 12228)
        koma1 = moodle_producer(session, queue, 12301)
        analysis2 = custom_producer(analysis.parse_main_page, session, queue)
        informatik1 = custom_producer(informatik.parse_main_page, session, queue)

        v_nus = video_portal.producer(session, queue, "d-itet", "2020", "spring", "227-0002-00L",
                                      pwd_username="bie-20s", pwd_password=settings.portal_nus2_pwd)

        v_inf = video_portal.producer(session, queue, "d-infk", "2020", "spring", "252-0848-00L",
                                      pwd_username="scw-20s", pwd_password=settings.portal_inf1_pwd)

        v_analysis = video_portal.producer(session, queue, "d-math", "2020", "spring", "401-0232-10L")
        v_koma = video_portal.producer(session, queue, "d-math", "2020", "spring", "401-0302-10L")

        producers_no_login = [
            asyncio.create_task(analysis2),
            asyncio.create_task(informatik1),
        ]

        if settings.use_video_portal:
            producers_portal = [
                asyncio.create_task(v_nus),
                asyncio.create_task(v_inf),
                asyncio.create_task(v_analysis),
                asyncio.create_task(v_koma),
            ]
        else:
            producers_portal = []

        await moodle.login_async(session)

        producers = [
            asyncio.create_task(nus2),
            asyncio.create_task(physik1),
            asyncio.create_task(koma1),
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
