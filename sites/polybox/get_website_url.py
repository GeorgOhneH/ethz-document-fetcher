from .constants import INDEX_URL


def get_website_url(poly_id, poly_type="s", **kwargs):
    return INDEX_URL + poly_type + "/" + poly_id
