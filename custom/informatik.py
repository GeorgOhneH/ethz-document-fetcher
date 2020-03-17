from custom.utils import validate_url


async def parse_main_page(session, queue, **kwargs):
    BASE_URL = "https://lec.inf.ethz.ch/itet/informatik1/2020/"

    links_to_pdf = {
        "Overlays": lambda x: "slides/lecture{}.pdf".format(x + 1),
        "Handout": lambda x: "slides/lecture{}.handout.pdf".format(x + 1),
        "Exercise": "dl/exercises/exercises{:02d}.pdf".format,
    }

    await validate_url(session, queue, links_to_pdf, BASE_URL, **kwargs)
