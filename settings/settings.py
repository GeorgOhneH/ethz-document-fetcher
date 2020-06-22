import argparse
import os
import logging
import copy

from settings.values import ConfigPath, ConfigList, ConfigBool, ConfigPassword, ConfigOptions, ConfigString
from settings.constants import SEPARATOR, ROOT_PATH

logger = logging.getLogger(__name__)


def get_key_value(f):
    for line in f.readlines():
        if SEPARATOR in line:
            key, value = [x.strip() for x in line.split(SEPARATOR)]
            yield key, value


def init_wrapper(func, values, parser):
    def wrapper(self, *args, **kwargs):
        if hasattr(self, "_values"):
            self._values.update(values)
        else:
            self._values = values
        self.parser = parser
        return func(self, *args, **kwargs)

    return wrapper


class SettingBase(type):
    argument_parser = argparse.ArgumentParser()

    def __new__(mcs, name, bases, attrs, **kwargs):
        values = {}
        new_attrs = {}
        for key, value in attrs.items():
            if isinstance(value, ConfigString):
                value.name = key
                values[key] = value

                value.set_parser(mcs.argument_parser)

                new_attrs[key] = property(lambda self, v_k=key: self._values[v_k].get(),
                                          lambda self, value, v_k=key: self._values[v_k].set(value))
            else:
                new_attrs[key] = value
        cls = super().__new__(mcs, name, bases, new_attrs)
        cls.__init__ = init_wrapper(cls.__init__, values, mcs.argument_parser)
        return cls


class Settings(metaclass=SettingBase):
    def __init__(self):
        current_settings = {}
        path = self.get_file_path()
        if os.path.exists(path):
            with open(path, "r") as f:
                for key, file_value in get_key_value(f):
                    current_settings[key] = file_value

        for value in self:
            file_value = current_settings.get(value.name, None)
            if file_value is not None:
                value.load(file_value)
        args = self.parser.parse_args()
        for value in self:
            arg_value = getattr(args, value.name)
            if arg_value is not None:
                if not value.test(arg_value):
                    self.parser.error(f"{value.name} was not valid")
                setattr(self, value.name, arg_value)

    def get_file_path(self):
        return os.path.join(ROOT_PATH, self.__class__.__name__.lower() + ".config")

    def __iter__(self):
        return iter(self._values.values())

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if v is self.parser:
                setattr(result, k, v)
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result

    def clear_buffer(self):
        for value in self:
            value.set_buffer(None)

    def apply_buffer(self):
        for value in self:
            value.apply_buffer()

    def check_if_valid(self):
        path = self.get_file_path()
        if not os.path.exists(path):
            logger.warning(f"Did not found a {path} file")
            return False
        for value in self:
            if not value.is_valid():
                logger.warning(f"Setting was not valid. Error Msg: {value.msg}")
                return False
        return True

    def save(self):
        path = self.get_file_path()
        with open(path, "w+") as f:
            for value in self:
                string = value.save()
                if string is not None:
                    f.write(f"{value.name}{SEPARATOR}{string}\n")


class GlobalSettings(Settings):
    loglevel = ConfigOptions(default="DEBUG", options=["ERROR", "WARNING", "INFO", "DEBUG"])


class SiteSettings(Settings):
    username = ConfigString(optional=True)
    password = ConfigPassword(optional=True)
    base_path = ConfigPath(ony_folder=True)
    # template_path = ConfigPath(absolute=False, default=os.path.join("templates", "FS2020", "itet", "semester2.yml"), file_extensions=["yml"])
    allowed_extensions = ConfigList(default=[], optional=True)
    forbidden_extensions = ConfigList(default=["video"], optional=True)
    keep_replaced_files = ConfigBool(default=False)
    force_download = ConfigBool(default=False, active_func=lambda: False)
