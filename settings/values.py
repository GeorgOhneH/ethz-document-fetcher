import base64

from settings.constants import *


class ConfigString(object):
    def __init__(self, default=None, active_func=lambda: True, depends_on=None, optional=False):
        if depends_on is None:
            depends_on = []
        self.depends_on = depends_on
        self._value = None
        self.set(None, default)
        self.active_func = active_func
        self.name = None
        self.optional = optional
        self.error_on_load = False
        self.msg = ""

    def get(self, obj=None):
        return self._value

    def set(self, obj, value):
        self._value = value

    def convert_from_prompt(self, value):
        return value

    def test(self, value):
        if value or self.optional:
            return self._test(value)
        self.msg = "Value must be set"
        return False

    def _test(self, value):
        return True

    def load(self, value):
        self._value = self._load(value)

    def _load(self, value):
        return value

    def save(self):
        if self.test(self._value):
            return self._save()
        raise ValueError("Tried to save an invalid ConfigObject")

    def _save(self):
        return self._value

    def is_active(self):
        return self.active_func() and all([x.get_value() for x in self.depends_on])

    def is_set(self):
        return self._value or self.optional

    def is_valid(self):
        if not self.is_active():
            return True
        if self.is_set() and self.test(self._value):
            return True
        return False

    def _middle_prompt(self):
        return ""

    def _get_current(self):
        return f" (current: {self._save()})" if self.is_valid() else ""

    def get_user_prompt(self):
        return f"Please enter the value for {self.name}{self._middle_prompt()}{self._get_current()}: "


class ConfigPath(ConfigString):
    def __init__(self, absolute=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.absolute = absolute

    def _test(self, value):
        if self.absolute or os.path.isabs(value):
            if not os.path.isabs(value):
                self.msg = "please enter an absolute path"
                return False
            path = value
        else:
            base_path = os.path.dirname(os.path.dirname(__file__))
            path = os.path.join(base_path, value)

        if not os.path.exists(path):
            self.msg = "please enter a valid path, which exists"
            return False
        return True


class ConfigPassword(ConfigString):
    def _load(self, value):
        return base64.b64decode(value).decode("utf-8")

    def _save(self):
        return base64.b64encode(self._value.encode("utf-8")).decode("utf-8")

    def _get_current(self):
        if self.get():
            censored = self.get()[0] + "*" * (len(self.get()) - 1)
            return f" (current: {censored})"
        return ""

    def get_user_prompt(self):
        return f"Please enter your password{self._get_current()} (password is not shown): "


class ConfigBool(ConfigString):
    def get(self, obj=None):
        return self._value and self.is_active()

    def test(self, value):
        return True

    def _test(self, value):
        return True

    def _load(self, value):
        return "y" in value

    def _save(self):
        return "yes" if self._value else "no"

    def is_set(self):
        return True

    def convert_from_prompt(self, value):
        return "y" in value

    def get_user_prompt(self):
        string_value = "yes" if self.get() else "no"
        current = f" (current: {string_value}) (yes/no)"

        return f"Please enter the bool for {self.name}{current}: "


class ConfigOption(ConfigString):
    def __init__(self, options, default="", **kwargs):
        if default and default not in options:
            raise ValueError("default not in options")
        super().__init__(default=default, **kwargs)
        self.options = options

    def _test(self, value):
        if value in self.options:
            return True
        self.msg = f"please enter a value from these options: {self.options}"
        return False

    def get_user_prompt(self):
        return f"Please enter the value for the {self.name} (options: {self.options}){self._get_current()}: "


class ConfigList(ConfigString):
    def _save(self):
        if not self._value:
            return "[]"
        result = "["
        for x in self._value[:-1]:
            result += str(x) + ", "
        result += self._value[-1] + "]"
        return result

    def _load(self, value):
        if not value:
            return []

        if value[0] != "[" or value[-1] != "]":
            self.error_on_load = True
            return []

        return [x.strip() for x in value[1:-1].split(",") if x.strip()]

    def convert_from_prompt(self, value):
        value = value.strip()
        if value and (value[0] != "[" or value[-1] != "]"):
            self.msg = "Not valid format"
            return None
        return self._load(value)

    def _test(self, value):
        if value is None:
            return False
        if not isinstance(value, list):
            raise ValueError("Value must be a list")
        return True

    def _middle_prompt(self):
        return " (format: [value1,value2,etc..] (empty is []))"
