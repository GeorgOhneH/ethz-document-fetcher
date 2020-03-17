import json
import os
from pathlib import Path
import base64
from settings import settings


def get_basic_auth_header():
    auth_string = (settings.username + ':' + settings.password).encode("utf-8")
    auth_string = base64.b64encode(auth_string).decode("utf-8")
    return {
        "Authorization": f"Basic {auth_string}",
    }


async def check_url_reference(session, url, url_reference_path):
    url_reference = load_url_reference(url_reference_path)
    new_url = url_reference.get(url, None)

    if new_url is None:
        async with session.get(url, raise_for_status=False) as response:
            new_url = str(response.url)
        url_reference[url] = new_url
        save_url_reference(url_reference, url_reference_path)

    return new_url


def save_txt(section, path):
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "w+") as f:
        f.write(str(section))


def load_txt(path):
    with open(path, "r") as f:
        return f.read()


def load_url_reference(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_url_reference(url_reference, path):
    with open(path, "w+") as f:
        return json.dump(url_reference, f)
