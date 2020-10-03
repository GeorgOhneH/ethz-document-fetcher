import argparse
import logging
import os

from settings.config import ConfigBase, Configs
from settings.config_objs import ConfigPath, ConfigListString, ConfigBool, ConfigPassword, \
    ConfigOptions, ConfigString, ConfigInt
from settings.constants import ROOT_PATH
from settings.constants import SEPARATOR, CONFIG_PATH

logger = logging.getLogger(__name__)


def get_key_value(f):
    for line in f.readlines():
        if SEPARATOR in line:
            key, value = [x.strip() for x in line.split(SEPARATOR)]
            yield key, value


class SettingBase(ConfigBase):
    argument_parser = argparse.ArgumentParser()

    def __new__(mcs, name, bases, attrs, **kwargs):
        cls = super().__new__(mcs, name, bases, attrs, **kwargs)
        for key, value in attrs.items():
            if isinstance(value, ConfigString):
                config_obj = value
                config_obj.set_parser(mcs.argument_parser)

        cls.parser = mcs.argument_parser
        return cls


class Settings(Configs, metaclass=SettingBase):
    def __init__(self):
        super().__init__()
        current_settings = {}
        path = self.get_file_path()
        if os.path.exists(path):
            with open(path, "r") as f:
                for key, file_value in get_key_value(f):
                    current_settings[key] = file_value

        for config_obj in self:
            file_value = current_settings.get(config_obj.name, None)
            if file_value is not None:
                config_obj.load(file_value)
        args = self.parser.parse_args()
        for config_obj in self:
            arg_value = getattr(args, config_obj.name)
            if arg_value is not None:
                if not config_obj.test(arg_value):
                    self.parser.error(f"{config_obj.name} was not valid")
                setattr(self, config_obj.name, arg_value)

    def get_file_path(self):
        return os.path.join(CONFIG_PATH, self.__class__.__name__.lower() + ".config")

    def save(self):
        logger.debug(f"Saving settings: {self.__class__.__name__}")
        path = self.get_file_path()
        with open(path, "w+") as f:
            for config_obj in self:
                string = config_obj.save()
                if string is not None:
                    f.write(f"{config_obj.name}{SEPARATOR}{string}\n")


class AdvancedSettings(Settings):
    NAME = "Advanced"
    loglevel = ConfigOptions(default="DEBUG",
                             options=["ERROR", "WARNING", "INFO", "DEBUG"],
                             gui_name="Loglevel",
                             require_restart=True)
    check_for_updates = ConfigBool(default=True, gui_name="Check for Updates")


class TemplatePathSettings(Settings):
    template_path = ConfigPath(default=os.path.join(ROOT_PATH, "templates", "example.yml"),
                               file_extensions=["yml"])


def highlight_difference_active(instance, from_widget, parent):
    if from_widget:
        keep_replaced_files = instance.get_config_obj("keep_replaced_files").get_from_widget()
    else:
        keep_replaced_files = instance.get_config_obj("keep_replaced_files").get()

    return keep_replaced_files


class SiteSettings(Settings):
    NAME = "Download"
    username = ConfigString(optional=True, gui_name="Username")
    password = ConfigPassword(optional=True, gui_name="Password")
    base_path = ConfigPath(only_folder=True, gui_name="Save Path")
    allowed_extensions = ConfigListString(default=[], optional=True, gui_name="Allowed Extensions",
                                          hint_text="Add 'video' for all video types.")
    forbidden_extensions = ConfigListString(default=["video"], optional=True, gui_name="Forbidden Extensions",
                                            hint_text="Add 'video' for all video types.")
    keep_replaced_files = ConfigBool(default=True, gui_name="Keep Replaced Files")
    highlight_difference = ConfigBool(default=True, active_func=highlight_difference_active, gray_out=True,
                                      gui_name="Add Highlight Difference to Replaced Files (pdf only, can be cpu heavy)")
    force_download = ConfigBool(default=False, gui_name="Force Download")
    conn_limit = ConfigInt(minimum=0, default=50, gui_name="Maximum Number of Connections",
                           hint_text="0 for unlimited")
    conn_limit_per_host = ConfigInt(minimum=0, default=5, gui_name="Maximum Number of Connections per Host",
                                    hint_text="0 for unlimited")


class GUISettings(Settings):
    NAME = "GUI"

