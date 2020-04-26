import aai_logon
from .constants import *


async def login(session):
    async with session.post(AUTH_URL, data=IDP_DATA) as response:
        text = await response.text()
    await aai_logon.login(session, text, aai_logon.MOODLE_URL)


async def test_connection(session):
    async with session.get(BASE_URL) as response:
        content = await response.read()

    return b"Moodle Course: Hier k\xc3\xb6nnen Sie sich anmelden" not in content

