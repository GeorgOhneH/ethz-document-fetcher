import argparse
import logging
import os

import settings.utils
from gui.constants import ALL_THEMES, THEME_NATIVE, SITES_URL
from settings.config import ConfigBase, Configs
from settings.config_objs import ConfigPath, ConfigListString, ConfigBool, ConfigPassword, \
    ConfigOptions, ConfigString, ConfigInt
from settings.constants import ROOT_PATH, SEPARATOR

logger = logging.getLogger(__name__)


def get_key_value(f):
    for line in f.readlines():
        if SEPARATOR in line:
            key, value = [x.strip() for x in line.split(SEPARATOR)]
            yield key, value


class SettingBase(ConfigBase):
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--app-data-path")

    def __new__(mcs, name, bases, attrs, **kwargs):
        cls = super().__new__(mcs, name, bases, attrs, **kwargs)
        for key, value in attrs.items():
            if isinstance(value, ConfigString):
                config_obj = value
                config_obj.set_parser(mcs.argument_parser)

        cls.parser = mcs.argument_parser
        return cls


class Settings(Configs, metaclass=SettingBase):
    NAME = "Setting"

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

    def get_file_path(self) -> str:
        return os.path.join(settings.utils.get_config_path(), self.__class__.__name__.lower() + ".config")

    def save(self):
        logger.debug(f"Saving settings: {self.__class__.__name__}")
        path = self.get_file_path()
        with open(path, "w+") as f:
            for config_obj in self:
                string = config_obj.save()
                if string is not None:
                    f.write(f"{config_obj.name}{SEPARATOR}{string}\n")


class BehaviorSettings(Settings):
    NAME = "Behavior"
    loglevel = ConfigOptions(default="DEBUG",
                             options=["ERROR", "WARNING", "INFO", "DEBUG"],
                             gui_name="Loglevel",
                             require_restart=True)
    check_for_updates = ConfigBool(default=True, gui_name="Check for Updates")


class TemplatePathSettings(Settings):
    template_path = ConfigPath(default=os.path.join(ROOT_PATH, "templates", "example.yml"),
                               file_extensions=["yml"])


def highlight_size_limit_active(instance, from_widget, parent):
    if from_widget:
        highlight_difference = instance.get_config_obj("highlight_difference").get_from_widget()
    else:
        highlight_difference = instance.get_config_obj("highlight_difference").get()

    return highlight_difference


class DownloadSettings(Settings):
    NAME = "Download"
    save_path = ConfigPath(only_folder=True, gui_name="Save Path")
    username = ConfigString(optional=True, gui_name="Username")
    password = ConfigPassword(optional=True, gui_name="Password")
    keep_replaced_files = ConfigBool(default=True, gui_name="Keep Replaced Files")

    highlight_difference = ConfigBool(default=True,
                                      gray_out=True,
                                      gui_name="Highlight Difference between old and new Files (pdf only)",
                                      hint_text="Creates a side-by-side view of the old and "
                                                "new pdf, where the differences are highlighted.")

    highlight_page_limit = ConfigInt(default=50,
                                     minimum=0,
                                     active_func=highlight_size_limit_active,
                                     gray_out=True,
                                     gui_name="Page Limit for Highlights",
                                     hint_text="Only creates highlights if the pdf page "
                                               "count is below the limit. (0 for unlimited)")
    force_download = ConfigBool(default=False,
                                gui_name="Force Download",
                                hint_text=f"This will check every file for updates. Affects only modules, "
                                          f"which don't already support updates.<br>"
                                          f"See <a href=\"{SITES_URL}\">this</a> for a list "
                                          f"on which modules are affected.")
    allowed_extensions = ConfigListString(default=[], optional=True, gui_name="Allowed Extensions",
                                          hint_text="Add 'video' for all video types.")
    forbidden_extensions = ConfigListString(default=[], optional=True, gui_name="Forbidden Extensions",
                                            hint_text="Add 'video' for all video types.")
    conn_limit = ConfigInt(minimum=0, default=50, gui_name="Maximum Number of Connections",
                           hint_text="0 for unlimited")
    conn_limit_per_host = ConfigInt(minimum=0, default=5, gui_name="Maximum Number of Connections per Host",
                                    hint_text="0 for unlimited")


class GUISettings(Settings):
    NAME = "GUI"

    theme = ConfigOptions(default=THEME_NATIVE,
                          options=ALL_THEMES,
                          gui_name="Theme")
