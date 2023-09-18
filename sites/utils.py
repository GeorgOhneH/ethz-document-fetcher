import logging
import re

from core.downloader import is_extension_forbidden
from sites import zoom, polybox

logger = logging.getLogger(__name__)


def remove_vz_id(name):
    return re.sub(r"[0-9]{3}-[0-9]{4}-[0-9]{2}L\s*", "", name)


async def process_single_file_url(session, queue, base_path, download_settings, url, name, password=None):
    if "polybox" in url:
        poly_type, poly_id = [x.strip() for x in url.split("/") if x.strip() != ""][3:5]
        await polybox.parse_single_file(session,
                                        queue,
                                        base_path,
                                        poly_id,
                                        name=name,
                                        poly_type=poly_type,
                                        password=password)

    elif "zoom.us/rec/play" in url or "zoom.us/rec/share" in url:
        # TODO: fix zoom
        return
        allowed_extensions = []
        if download_settings.allowed_extensions:
            allowed_extensions += download_settings.allowed_extensions
        if queue.consumer_kwargs["allowed_extensions"]:
            allowed_extensions += queue.consumer_kwargs["allowed_extensions"]

        forbidden_extensions = []
        if download_settings.forbidden_extensions:
            forbidden_extensions += download_settings.forbidden_extensions
        if queue.consumer_kwargs["forbidden_extensions"]:
            forbidden_extensions += queue.consumer_kwargs["forbidden_extensions"]

        if is_extension_forbidden("mp4", allowed_extensions, forbidden_extensions):
            return

        await zoom.download(session=session,
                            queue=queue,
                            base_path=base_path,
                            url=url,
                            file_name=name,
                            password=password)
