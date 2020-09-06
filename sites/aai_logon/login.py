import asyncio
import html
import re

from aiohttp import ClientSession

from core.exceptions import LoginError
from .constants import *

locks = {}


def get_sso_data(site_settings):
    return {
        ":formid": "_content_main_de_jcr_content_par_start",
        ":formstart": "/content/main/de/jcr:content/par/start",
        "_charset_": "UTF-8",
        "form_flavour": "eth_form",
        "j_username": site_settings.username,
        "j_password": site_settings.password,
        "_eventId_proceed": "",
    }


async def login(session: ClientSession, site_settings, url, data):
    if id(session) not in locks:
        lock = asyncio.Lock()
        locks[id(session)] = lock
    else:
        lock = locks[id(session)]

    async with lock:
        async with session.post(url, data=data) as resp:
            text = await resp.text()

        if "SAMLResponse" not in text:

            action_url = re.search("""<form .*action="(.+)" method="post">""", text)[1]
            action_url = html.unescape(action_url)

            async with session.post(BASE_URL + action_url, data=LOCAL_STORAGE_DATA) as resp:
                text = await resp.text()

            action_url = re.search("""<form action="(.+)" method="post">""", text)[1]
            action_url = html.unescape(action_url)

            async with session.post(BASE_URL + action_url, data=get_sso_data(site_settings)) as resp:
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
            pass
