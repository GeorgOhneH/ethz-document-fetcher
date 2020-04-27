import aai_logon
from ilias.constants import *


async def login(session):
    async with session.get(LOGIN_URL) as response:
        response_url = response.url

    await aai_logon.login(session, response_url, IDP_DATA)
