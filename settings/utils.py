import logging


logger = logging.getLogger(__name__)


def apply_value_from_widget(settings):
    for value in settings:
        if not value.is_valid_from_widget():
            logger.debug(f"{value.name} is not valid. msg: {value.msg}")
            return
    for value in settings:
        value.set_from_widget()
    settings.save()


