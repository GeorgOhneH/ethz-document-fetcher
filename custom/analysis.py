from .utils import validate_url


async def parse_main_page(session, queue, folder_name=None):

    BASE_URL = "https://metaphor.ethz.ch/x/2020/fs/401-0232-10L/"

    links_to_pdf = {
        "Serie": "serie/Serie{:02d}.pdf".format,
        "Loesung": "serie/Loesung{:02d}.pdf".format,
    }

    await validate_url(session, queue, links_to_pdf, BASE_URL, folder_name)
