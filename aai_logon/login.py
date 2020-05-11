import asyncio
import html
import re

from aiohttp import ClientSession

from core.exceptions import LoginError
from .constants import *

lock = asyncio.Lock()


async def login(session: ClientSession, url, data):
    async with lock:
        async with session.post(url, data=data) as resp:
            text = await resp.text()

        if "you must press the Continue button once to proceed" not in text:
            action_url = re.search("""<form action="(.+)" method="post">""", text)[1]
            action_url = html.unescape(action_url)

            async with session.post(BASE_URL + action_url, data=SSO_DATA) as resp:
                text = await resp.text()
        try:
            sam_url = re.search("""<form action="(.+)" method="post">""", text)[1]
            sam_url = html.unescape(sam_url)
            ssm = re.search("""name="RelayState" value="(.+)"/>""", text)[1]
            ssm = html.unescape(ssm)
            sam = re.search("""name="SAMLResponse" value="(.+)"/>""", text)[1]
            sam = html.unescape(sam)
        except TypeError as e:
            raise LoginError("Wasn't able to log in. Please check that your username and password are correct") from e

        saml_data = {
            "RelayState": ssm,
            "SAMLResponse": sam,
        }

        async with session.post(f"{sam_url}", data=saml_data) as resp:
            await resp.text()
