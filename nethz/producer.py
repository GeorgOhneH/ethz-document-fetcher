from bs4 import BeautifulSoup
from constants import BEAUTIFUL_SOUP_PARSER
from utils import safe_path_join


async def producer(session, queue, url, base_path, allowed_extensions=None):
    if url[-1] != "/":
        url += "/"

    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

    links = soup.find_all("a")
    for link in links:
        href = link.get("href")
        if href != str(link.string).strip():
            continue

        if href[-1] == "/":
            href = href[:-1]

        path = safe_path_join(base_path, href)

        if "." in href:
            extension = href.split(".")[-1]
            if allowed_extensions is None or extension in allowed_extensions:
                await queue.put({"url": url + href, "path": path})
        else:
            await producer(session, queue, url + href, path, allowed_extensions=allowed_extensions)
