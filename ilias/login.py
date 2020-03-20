from ilias.constants import *
import aai_logon


async def login(session):
    async with session.get(LOGIN_URL) as response:
        response_url = response.url

    async with session.post(response_url, data=IDP_DATA) as response:
        text = await response.text()

    await aai_logon.login(session, text, aai_logon.ILIAS_URL)
