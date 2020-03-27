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

    def get_user_prompt(self):
        current = f" (current: {self.get_value()})" if self.get_value() else ""
        return f"Please enter the {self.__class__.__name__.lower()} for {self.name}{current}: "


class Path(String):
    def get_value(self, obj=None):
        return self._value

    def set_value(self, obj, value):
        self.test_value(value)
        self._value = value

    def test_value(self, value):
        if value and not os.path.exists(value):
            raise InvalidPath("please enter a valid path, which exists")
        if value and not os.path.isabs(value):
            raise InvalidPath("please enter an absolute path")

    def is_set(self):
        try:
            self.test_value(self._value)
        except InvalidPath:
            return False
        return True


class Password(String):
    def get_value(self, obj=None):
        return base64.b64decode(self._value).decode("utf-8")

    def set_value(self, obj, value):
        self._value = base64.b64encode(value.encode("utf-8")).decode("utf-8")

    def get_user_prompt(self):
        return f"Please enter your password{self._get_current()} (password is not shown): "

    def _get_current(self):
        if self.get_value():
            censored = self.get_value()[0] + "*" * (len(self.get_value()) - 1)
            return f" (current: {censored})"
        return ""


class Bool(String):
    def get_value(self, obj=None):
        return "y" in self._value

    def set_value(self, obj, value):
        self._value = "yes" if "y" in value else "no"

    def load_value(self, value):
        self.set_value(None, value.lower())

    def is_set(self):
        return True

    def get_user_prompt(self):
        string_value = "yes" if self.get_value() else "no"
        current = f" (current: {string_value}) (yes/no)"

        return f"Please enter the bool for {self.name}{current}: "
