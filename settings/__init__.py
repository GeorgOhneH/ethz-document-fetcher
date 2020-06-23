import atexit

from settings.settings import GlobalSettings
from settings.values import ConfigPath
from settings import utils

global_settings = GlobalSettings()


atexit.register(utils.apply_value_from_widget, global_settings)
