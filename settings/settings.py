import argparse
import os
import logging

from settings.config_objs import ConfigPath, ConfigList, ConfigBool, ConfigPassword, ConfigOptions, ConfigString
from settings.constants import SEPARATOR, CONFIG_PATH
from settings.config import ConfigBase, Configs

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
        path = self.get_file_path()
        with open(path, "w+") as f:
            for config_obj in self:
                string = config_obj.save()
                if string is not None:
                    f.write(f"{config_obj.name}{SEPARATOR}{string}\n")


class GlobalSettings(Settings):
    NAME = "Global"
    loglevel = ConfigOptions(default="DEBUG", options=["ERROR", "WARNING", "INFO", "DEBUG"], gui_name="Loglevel")


class TemplatePathSettings(Settings):
    template_path = ConfigPath(absolute=False,
                               default=os.path.join("templates", "example.yml"),
                               file_extensions=["yml"])


class SiteSettings(Settings):
    NAME = "Site"
    username = ConfigString(optional=True, gui_name="Username")
    password = ConfigPassword(optional=True, gui_name="Password")
    base_path = ConfigPath(ony_folder=True, gui_name="Save Path")
    allowed_extensions = ConfigList(default=[], optional=True, gui_name="Allowed Extensions",
                                    hint_text="Add 'video' for all video types.")
    forbidden_extensions = ConfigList(default=["video"], optional=True, gui_name="Forbidden Extensions",
                                      hint_text="Add 'video' for all video types.")
    keep_replaced_files = ConfigBool(default=True, gui_name="Keep Replaced Files")
    highlight_difference = ConfigBool(default=True, gui_name="Add Highlight Difference to Replaced Files (pdf only)")
    force_download = ConfigBool(default=False, gui_name="Force Download")
