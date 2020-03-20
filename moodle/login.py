import aai_logon
from .constants import *


async def login(session, use_cache=False):
    file_path = os.path.join(CACHE_PATH, "session.pickle")

    if use_cache and os.path.exists(file_path):
        old_cookie_jar = session.cookie_jar
        session.cookie_jar.load(file_path)
        if await test_connection(session):
            return
        session.cookie_jar.clear()
        session.cookie_jar.update_cookies(old_cookie_jar)

    async with session.post(AUTH_URL, data=IDP_DATA) as response:
        text = await response.text()
    await aai_logon.login(session, text, aai_logon.MOODLE_URL)

    if use_cache:
        session.cookie_jar.save(file_path)


async def test_connection(session):
    async with session.get(BASE_URL) as response:
        content = await response.read()

    return b"Moodle Course: Hier k\xc3\xb6nnen Sie sich anmelden" not in content

