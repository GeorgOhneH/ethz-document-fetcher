import functools
import logging
import os
from pathlib import Path

import core.utils

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=None)
def get_config_path():
    config_path = os.path.join(core.utils.get_app_data_path(), "config")
    Path(config_path).mkdir(parents=True, exist_ok=True)
    return config_path


def apply_value_from_widget(settings):
    for value in settings:
        if not value.is_valid_from_widget():
            logger.debug(f"{value.name} is not valid. msg: {value.msg}")
            return
    for value in settings:
        value.set_from_widget()
    settings.save()
