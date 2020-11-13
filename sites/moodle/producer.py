from bs4 import BeautifulSoup

from core.constants import BEAUTIFUL_SOUP_PARSER
from core.exceptions import LoginError
from sites.moodle.parser import parse_main_page
from .constants import AUTH_URL
from settings.config_objs import ConfigList, ConfigDict, ConfigString, ConfigBool

PASSWORD_MAPPER_CONFIG = ConfigList(
    gui_name="Password Mapper",
    hint_text="If a polybox or zoom link requires a password, you can map the password with the name of the link.<br>"
              "The name parameter will be interpreted as a "
              "<a href=\"https://docs.python.org/3/library/re.html\">regrex expression</a>",
    optional=True,
    config_obj_default=ConfigDict(
        gui_name="",
        layout={
            "name": ConfigString(
                gui_name="Name",
            ),
            "password": ConfigString(
                gui_name="Password",
            ),
        }
    )
)


async def producer(session,
                   queue,
                   base_path,
                   site_settings,
                   id,
                   process_external_links=True,
                   keep_section_order=False,
                   password_mapper: PASSWORD_MAPPER_CONFIG = None):
    async with session.get(f"https://moodle-app2.let.ethz.ch/course/view.php?id={id}") as response:
        html = await response.read()
        if str(response.url) == AUTH_URL:
            raise LoginError("Module moodle isn't logged in")
    return await parse_main_page(session,
                                 queue,
                                 html,
                                 base_path,
                                 site_settings,
                                 id,
                                 process_external_links,
                                 keep_section_order,
                                 password_mapper)


async def get_folder_name(session, id, **kwargs):
    async with session.get(f"https://moodle-app2.let.ethz.ch/course/view.php?id={id}") as response:
        html = await response.read()
    soup = BeautifulSoup(html, BEAUTIFUL_SOUP_PARSER)

    header = soup.find("div", class_="page-header-headings")
    header_name = str(header.h1.string)
    return header_name
