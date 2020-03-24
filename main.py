import asyncio
import os

import aiohttp
from aiohttp import BasicAuth

import ilias
import polybox
import video_portal
import moodle
from settings import settings
from custom import analysis, informatik
from downloader import download_files
from custom.utils import collect_all_links


async def main():
    if not settings.check_if_set():
        raise ValueError("Please run 'python setup.py'")

    queue = asyncio.Queue()

    async with aiohttp.ClientSession(raise_for_status=True) as session:
        tiagos_path = os.path.join("401-0302-10L Komplexe Analysis FS2020", "tiagos")
        tiagos = collect_all_links(session, queue, "https://n.ethz.ch/~tiagos/download/2020/", tiagos_path)

        nus2 = moodle.producer(session, queue, 11838)
        physik1 = moodle.producer(session, queue, 12228)
        physik1_poly = polybox.producer(queue, "iSYMs1nnDAzDWtU",
                                        base_path=os.path.join("Physik 1 D-ITET (FS20)", "polybox"))
        koma1 = moodle.producer(session, queue, 12301)
        analysis2_moodle = moodle.producer(session, queue, 12611)
        ilias_path = os.path.join("401-0232-10L Analysis 2 FS2020", "ilias")
        analysis2_ilias = ilias.producer(session, queue, "187834", base_path=ilias_path)
        analysis2 = analysis.parse_main_page(session, queue, folder_name="401-0232-10L Analysis 2 FS2020")
        informatik1 = informatik.parse_main_page(session, queue, auth=BasicAuth(settings.username, settings.password))

        poly_nus_path = os.path.join("227-0002-00L Netzwerke und Schaltungen II FS2020", "Daniel Biek Polybox")
        poly_nus = polybox.producer(queue, "4YGUCHIXorTsvVL", poly_nus_path)
        poly_analysis_path = os.path.join("401-0232-10L Analysis 2 FS2020", "Jonas Wahlen Polybox")
        poly_analysis = polybox.producer(queue, "C8LWUyvLRUbh3zX", poly_analysis_path)

        if settings.use_video_portal:
            v_nus_2020 = video_portal.producer(session, queue, "d-itet", "2020", "spring", "227-0002-00L",
                                               pwd_username="bie-20s", pwd_password=settings.portal_nus2_2020_password)
            v_nus_2019 = video_portal.producer(session, queue, "d-itet", "2019", "spring", "227-0002-00L",
                                               pwd_username="bie-19s", pwd_password=settings.portal_nus2_2019_password)
            v_inf_2020 = video_portal.producer(session, queue, "d-infk", "2020", "spring", "252-0848-00L",
                                               pwd_username="scw-20s", pwd_password=settings.portal_inf1_2020_password)
            v_inf_2019 = video_portal.producer(session, queue, "d-infk", "2019", "autumn", "252-0847-00L",
                                               pwd_username="scw-19w", pwd_password=settings.portal_inf1_2019_password)
            v_analysis = video_portal.producer(session, queue, "d-math", "2020", "spring", "401-0232-10L")
            v_koma = video_portal.producer(session, queue, "d-math", "2020", "spring", "401-0302-10L")

            poly_nus_uebung_path = os.path.join(settings.video_portal_path, "NuS2 Übungen")
            poly_nus_uebung = polybox.producer(queue, "SU2lkCtdoLH3X1w", poly_nus_uebung_path,
                                               password=settings.nus2_poly_uebung)

            producers_portal = [
                asyncio.create_task(v_nus_2020),
                asyncio.create_task(v_nus_2019),
                asyncio.create_task(v_inf_2020),
                asyncio.create_task(v_inf_2019),
                asyncio.create_task(v_analysis),
                asyncio.create_task(v_koma),
                asyncio.create_task(poly_nus_uebung),
            ]
        else:
            producers_portal = []

        producers_no_login = [
            asyncio.create_task(analysis2),
            asyncio.create_task(informatik1),
            asyncio.create_task(poly_nus),
            asyncio.create_task(poly_analysis),
            asyncio.create_task(physik1_poly),
            asyncio.create_task(tiagos),
        ]

        await moodle.login(session)
        await ilias.login(session)

        producers = [
            asyncio.create_task(nus2),
            asyncio.create_task(physik1),
            asyncio.create_task(koma1),
            asyncio.create_task(analysis2_moodle),
            asyncio.create_task(analysis2_ilias),
            *producers_no_login,
            *producers_portal,
        ]

        consumers = [asyncio.create_task(download_files(session, queue)) for _ in range(20)]

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
