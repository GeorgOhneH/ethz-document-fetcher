from sites.ilias.constants import GOTO_URL


def get_website_url(ilias_id, **kwargs):
    return GOTO_URL + str(ilias_id)
