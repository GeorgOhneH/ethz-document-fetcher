from .constants import BASE_URL


def get_website_url(moodle_id, **kwargs):
    return BASE_URL + f"/course/view.php?id={moodle_id}"
