import asyncio
import warnings
from urllib.parse import urljoin

from aiohttp import ClientSession
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from core.exceptions import LoginError
from core.utils import get_beautiful_soup_parser
from .constants import *

locks = {}

MAX_REDIRECT_FORMS = 8


def _parse_form(html, base_url):
    with warnings.catch_warnings():
        # Some hops in ETH's login chain return XHTML; we only care about
        # the <form> tag, so the HTML parser is fine for that.
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
        soup = BeautifulSoup(html, get_beautiful_soup_parser())
    form = soup.find("form")
    if form is None:
        return None, None, None

    action = urljoin(base_url, form.get("action") or base_url)
    form_data = {inp["name"]: inp.get("value", "")
                 for inp in form.find_all("input") if inp.get("name")}
    return form, action, form_data


def _fill_credentials(form, download_settings, form_data):
    username_input = form.find("input", {"type": "text"}) or form.find("input", {"type": "email"})
    password_input = form.find("input", {"type": "password"})
    if username_input is None or password_input is None:
        return False

    form_data[username_input["name"]] = download_settings.username
    form_data[password_input["name"]] = download_settings.password
    return True


def _submit_form(session, form, action, form_data):
    # Respect the form's declared method: some hops (e.g. the final
    # SAML-redirect binding) require GET, not POST, or they 400.
    if (form.get("method") or "post").strip().lower() == "get":
        return session.get(action, params=form_data)
    return session.post(action, data=form_data)


async def login(session: ClientSession, download_settings, url, data):
    if id(session) not in locks:
        lock = asyncio.Lock()
        locks[id(session)] = lock
    else:
        lock = locks[id(session)]

    async with lock:
        async with session.post(url, data=data) as resp:
            text = await resp.text()
            current_url = str(resp.url)

        # ETH's login flow is a chain of auto-submitting forms (session/local
        # storage hops, the actual credential form, possibly more). We keep
        # following whatever form we're given until we reach the page that
        # carries the SAMLResponse back to the requesting site.
        for _ in range(MAX_REDIRECT_FORMS):
            if "SAMLResponse" in text:
                break

            form, action, form_data = _parse_form(text, current_url)
            if form is None:
                raise LoginError("Wasn't able to log in. The ETH login page had an unexpected format.")

            _fill_credentials(form, download_settings, form_data)

            async with _submit_form(session, form, action, form_data) as resp:
                text = await resp.text()
                current_url = str(resp.url)

            if resp.status >= 400 and "SAMLResponse" not in text:
                raise LoginError("Wasn't able to log in. Please check that your username and password are correct")
        else:
            raise LoginError("Wasn't able to log in. The ETH login page had an unexpected format.")

        form, sam_url, saml_data = _parse_form(text, current_url)
        try:
            assert "SAMLResponse" in saml_data
        except (AssertionError, TypeError) as e:
            raise LoginError("Wasn't able to log in. Please check that your username and password are correct") from e

        async with _submit_form(session, form, sam_url, saml_data) as resp:
            pass
