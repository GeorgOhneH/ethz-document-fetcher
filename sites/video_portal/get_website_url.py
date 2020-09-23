from .constants import BASE_URL


def get_website_url(department, year, semester, course_id, **kwargs):
    return f"{BASE_URL}{department}/{year}/{semester}/{course_id}"
