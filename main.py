from settings import settings
settings.init()

import aiohttp
import asyncio

from custom import analysis, informatik
from downloader import *


async def main():

    queue = asyncio.Queue()

    async with aiohttp.ClientSession(raise_for_status=True) as session:
        nus2 = moodle_producer(session, queue, 11838)
        physik1 = moodle_producer(session, queue, 12228)
        koma1 = moodle_producer(session, queue, 12301)
        analysis2 = custom_producer(analysis.parse_main_page, session, queue)
        informatik1 = custom_producer(informatik.parse_main_page, session, queue)

        await moodle.login_async(session)

        producers_no_login = [
            asyncio.create_task(analysis2),
            asyncio.create_task(informatik1),
        ]

        producers = [
            asyncio.create_task(nus2),
            asyncio.create_task(physik1),
            asyncio.create_task(koma1),
            *producers_no_login,
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
