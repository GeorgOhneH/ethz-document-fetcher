import base64

from .constants import *
from .exceptions import *


class String(object):
    def __init__(self, name, value="", active_func=lambda: True):
        self._value = value
        self.name = name
        self.active_func = active_func

    def get_value(self, obj=None):
        return self._value

    def set_value(self, obj, value):
        self._value = value

    def load_value(self, value):
        self._value = value

    def is_active(self):
        return self.active_func()

    def is_set(self):
        return self._value != ""


class Path(String):
    def get_value(self, obj=None):
        return self._value

    def set_value(self, obj, value):
        if value and not os.path.exists(value):
            raise InvalidPath("please enter a valid path, which exists")
        self._value = value

    def load_value(self, value):
        self.set_value(None, value)


class Password(String):
    def get_value(self, obj=None):
        return base64.b64decode(self._value).decode("utf-8")

    def set_value(self, obj, value):
        self._value = base64.b64encode(value.encode("utf-8")).decode("utf-8")


class Bool(String):
    def get_value(self, obj=None):
        return "y" in self._value

    def set_value(self, obj, value):
        self._value = "yes" if "y" in value else "no"

    def load_value(self, value):
        self.set_value(None, value.lower())

    def is_set(self):
        return True
