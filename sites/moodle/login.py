from .constants import *
from .. import aai_logon


async def login(session, site_settings, **kwargs):
    await aai_logon.login(session, site_settings, AUTH_URL, IDP_DATA)


