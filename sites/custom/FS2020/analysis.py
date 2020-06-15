from sites.custom.utils import validate_url

BASE_URL = "https://metaphor.ethz.ch/x/2020/fs/401-0232-10L/"


async def parse_main_page(session, queue, base_path):
    links_to_pdf = {
        "Serie": "serie/Serie{:02d}.pdf".format,
        "Loesung": "serie/Loesung{:02d}.pdf".format,
    }

    await validate_url(session, queue, links_to_pdf, BASE_URL, base_path)
