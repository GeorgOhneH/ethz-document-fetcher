import re

from aiohttp import ClientSession

from .constants import *


async def login_async(session: ClientSession, response_text: str):
    jsessionid = re.search("jsessionid=.*=e1s1", response_text).group()

    async with session.post(f"{SSO_URL};{jsessionid}", data=SSO_DATA) as resp:
        text = await resp.text()

    try:
        match = re.search("""name="RelayState" value="ss&#x3a;mem&#x3a;(.*)"/>""", text)
        ssm = match.group(1)

        match = re.search("""name="SAMLResponse" value="(.*)"/>""", text)
        sam = match.group(1)
    except AttributeError:
        raise EnvironmentError("Wasn't able to log in. Please check that your username and password are correct")

    saml_data = {
        "RelayState": f"ss:mem:{ssm}",
        "SAMLResponse": sam,
    }

    async with session.post(f"{SAML_URL}", data=saml_data) as resp:
        resp.raise_for_status()
