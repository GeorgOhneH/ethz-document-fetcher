import argparse

from .values import *


def get_key_value(f):
    for line in f.readlines():
        if SEPARATOR in line:
            key, value = [x.strip() for x in line.split(SEPARATOR)]
            yield key, value


class SettingBase(type):
    def __new__(mcs, name, bases, attrs, **kwargs):
        values = {}
        for key, value in attrs.items():
            if isinstance(value, ConfigString):
                value.name = key
                attrs[key] = property(value._get, value._set)
                values[key] = value
        attrs["_values"] = values
        return super().__new__(mcs, name, bases, attrs)


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

    def check_if_valid(self):
        if not os.path.exists(SETTINGS_PATH):
            logger.warning("Did not found a settings.config file")
            return False
        for value in self:
            if not value.is_valid():
                return False
        return True

    def save(self):
        with open(SETTINGS_PATH, "w+") as f:
            for value in self:
                string = value.save()
                if string is not None:
                    f.write(f"{value.name}{SEPARATOR}{string}\n")


class AppSettings(Settings):
    username = ConfigString(optional=True)
    password = ConfigPassword(optional=True)
    base_path = ConfigPath(default=os.getcwd())
    template_path = ConfigPath(absolute=False, default=os.path.join("templates", "FS2020", "itet", "semester2.yml"))
    loglevel = ConfigOption(default="DEBUG", options=["ERROR", "WARNING", "INFO", "DEBUG"])
    allowed_extensions = ConfigList(default=[], optional=True)
    forbidden_extensions = ConfigList(default=["video"], optional=True)
    keep_replaced_files = ConfigBool(default=False)
    force_download = ConfigBool(default=False, active_func=lambda: False)
