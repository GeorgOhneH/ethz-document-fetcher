import os

from bs4 import BeautifulSoup

from core.constants import BEAUTIFUL_SOUP_PARSER
from core.utils import safe_path_join


async def validate_url(session, queue, links_to_pdf, base_url, base_path, **kwargs):
    async with session.get(base_url, **kwargs) as response:
        html = await response.text()

    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

    all_urls_from_site = set([])

    links = soup.find_all("a")
    for link in links:
        all_urls_from_site.add(link.get("href"))

    for i in range(20):
        path = os.path.join(base_path, "Woche {}".format(i))
        for name, url in links_to_pdf.items():
            real_url = url(i)
            if real_url not in all_urls_from_site:
                continue

            item_path = os.path.join(path, name + f" {i}.pdf")
            await queue.put({"path": item_path, "url": base_url + real_url, "session_kwargs": kwargs})


async def collect_all_links(session, queue, url, base_path, valid_extensions=None):
    if valid_extensions is None:
        valid_extensions = ['pdf', 'mp4']

    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

    links = soup.find_all("a")
    for link in links:
        href = link.get("href")
        if "." not in href:
            continue

        name, extension = href.split(".")
        if extension not in valid_extensions:
            continue
        await queue.put({"url": url + href, "path": safe_path_join(base_path, href)})
