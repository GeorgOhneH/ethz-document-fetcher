import atexit

from settings import utils
from settings.config_objs import ConfigPath
from settings.settings import GlobalSettings

global_settings = GlobalSettings()


atexit.register(utils.apply_value_from_widget, global_settings)
