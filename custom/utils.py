import os

from bs4 import BeautifulSoup


async def validate_url(session, queue, links_to_pdf, base_url, folder_name=None, **kwargs):
    async with session.get(base_url, **kwargs) as response:
        html = await response.text()

    soup = BeautifulSoup(html, "lxml")

    header_name = str(soup.title.string) if folder_name is None else folder_name

    all_urls_from_site = set([])

    links = soup.find_all("a")
    for link in links:
        all_urls_from_site.add(link.get("href"))

    for i in range(20):
        path = os.path.join(header_name, "Woche {}".format(i))
        for name, url in links_to_pdf.items():
            real_url = url(i)
            if real_url not in all_urls_from_site:
                continue

            item_path = os.path.join(path, name + f" {i}.pdf")
            await queue.put({"path": item_path, "url": base_url + real_url, "kwargs": kwargs})
