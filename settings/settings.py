import argparse
import os
import logging
import copy

from settings.values import ConfigPath, ConfigList, ConfigBool, ConfigPassword, ConfigOptions, ConfigString
from settings.constants import SEPARATOR, SETTINGS_PATH

logger = logging.getLogger(__name__)


def get_key_value(f):
    for line in f.readlines():
        if SEPARATOR in line:
            key, value = [x.strip() for x in line.split(SEPARATOR)]
            yield key, value


def init_wrapper(func, values):
    def wrapper(self, *args, **kwargs):
        if hasattr(self, "_values"):
            self._values.update(values)
        else:
            self._values = values
        return func(self, *args, **kwargs)
    return wrapper


class SettingBase(type):
    def __new__(mcs, name, bases, attrs, **kwargs):
        values = {}
        new_attrs = {}
        for key, value in attrs.items():
            if isinstance(value, ConfigString):
                value.name = key
                values[key] = value

                new_attrs[key] = property(lambda self, v_k=key: self._values[v_k].get(),
                                          lambda self, value, v_k=key: self._values[v_k].set(value))
            else:
                new_attrs[key] = value
        cls = super().__new__(mcs, name, bases, new_attrs)
        cls.__init__ = init_wrapper(cls.__init__, values)
        return cls


class Settings(metaclass=SettingBase):
    def __init__(self):
        current_settings = {}
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r") as f:
                for key, file_value in get_key_value(f):
                    current_settings[key] = file_value

        parser = argparse.ArgumentParser()
        for value in self:
            value.set_parser(parser)
            file_value = current_settings.get(value.name, None)
            if file_value is not None:
                value.load(file_value)
        args = parser.parse_args()
        for value in self:
            arg_value = getattr(args, value.name)
            if arg_value is not None:
                if not value.test(arg_value):
                    parser.error(f"{value.name} was not valid")
                setattr(self, value.name, arg_value)

    def __iter__(self):
        return iter(self._values.values())

    def clear_buffer(self):
        for value in self:
            value.set_buffer(None)

    def apply_buffer(self):
        for value in self:
            value.apply_buffer()

    def check_if_valid(self):
        if not os.path.exists(SETTINGS_PATH):
            logger.warning("Did not found a settings.config file")
            return False
        for value in self:
            if not value.is_valid():
                logger.warning(f"Setting was not valid. Error Msg: {value.msg}")
                return False
        return True

    def save(self):
        with open(SETTINGS_PATH, "w+") as f:
            for value in self:
                string = value.save()
                if string is not None:
                    f.write(f"{value.name}{SEPARATOR}{string}\n")


class GlobalSettings(Settings):
    loglevel = ConfigOptions(default="DEBUG", options=["ERROR", "WARNING", "INFO", "DEBUG"])


class SiteSettings(Settings):
    username = ConfigString(optional=True)
    password = ConfigPassword(optional=True)
    base_path = ConfigPath(default=os.getcwd(), ony_folder=True)
    # template_path = ConfigPath(absolute=False, default=os.path.join("templates", "FS2020", "itet", "semester2.yml"), file_extensions=["yml"])
    allowed_extensions = ConfigList(default=[], optional=True)
    forbidden_extensions = ConfigList(default=["video"], optional=True)
    keep_replaced_files = ConfigBool(default=False)
    force_download = ConfigBool(default=False, active_func=lambda: False)
