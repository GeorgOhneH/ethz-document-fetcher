from .constants import *
from .. import aai_logon


async def login(session, download_settings, **kwargs):
    await aai_logon.login(session, download_settings, AUTH_URL, IDP_DATA)


