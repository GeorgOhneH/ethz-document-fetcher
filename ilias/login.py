import aai_logon
from ilias.constants import *

import time


async def login(session):
    async with session.get(LOGIN_URL) as response:
        response_url = response.url
        # We read the response, because on some system we get
        # a silent ssl error and if we don't read the response
        # the whole program freezes for 20 seconds. (No idea why)
        await response.read()

    await aai_logon.login(session, response_url, IDP_DATA)
