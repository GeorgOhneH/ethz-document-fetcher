import os
import errno
import sys
import base64
from .exceptions import InvalidPath

ERROR_INVALID_NAME = 123


class Settings(object):
    def __init__(self):
        self.separator = ":="
        self.FOLDER_PATH = os.path.dirname(__file__)
        self.BASE_PATH = os.path.dirname(self.FOLDER_PATH)
        self.SETTINGS_PATH = os.path.join(self.BASE_PATH, "settings.config")
        self.TEMPLATE_PATH = os.path.join(self.FOLDER_PATH, "settings.config.template")
        self.init()

    def init(self, raise_exception=True):
        if raise_exception and not os.path.exists(self.SETTINGS_PATH):
            raise EnvironmentError("Please run 'python setup.py")
        self.init_attributes(raise_exception)

    def init_attributes(self, raise_exception):
        path = self.SETTINGS_PATH
        if not os.path.exists(path):
            path = self.TEMPLATE_PATH

        with open(path, "r") as f:
            for key, value in self.get_key_value(f.readlines()):
                if raise_exception:
                    self.test_key_value(key, value)
                setattr(self, key, value)

    def test_key_value(self, key, value):
        if "path" in key:
            if value and not os.path.exists(value):
                raise InvalidPath(f"The ({key}: {value}) in settings.config is not a valid path")

    def get_key_value(self, line_gen):
        for line in line_gen:
            if self.separator in line:
                key, value = [x.strip() for x in line.split(self.separator)]
                if "password" in key:
                    value = base64.b64decode(value).decode("utf-8")
                elif "use_" in key:
                    value = True if value.lower() == "y" or value.lower() == "yes" else False
                yield key, value

    def get_settings(self):
        settings = {}
        for path in [self.TEMPLATE_PATH, self.SETTINGS_PATH]:
            if os.path.exists(path):
                with open(path, "r") as f:
                    for key, value in self.get_key_value(f.readlines()):
                        settings[key] = value

        return settings

    def set_settings(self, data):
        with open(self.SETTINGS_PATH, "w+") as f:
            for key, value in data.items():
                if "password" in key:
                    value = base64.b64encode(value.encode("utf-8")).decode("utf-8")
                elif "use_" in key:
                    value = "yes" if value else "no"

                f.write(f"{key}{self.separator}{value}\n")

