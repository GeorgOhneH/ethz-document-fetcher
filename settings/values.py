import base64
import logging

from settings.constants import *

logger = logging.getLogger(__name__)


class ConfigString(object):
    TYPE = str

    def __init__(self, default=None, active_func=lambda: True, depends_on=None, optional=False):
        if depends_on is None:
            depends_on = []
        self.depends_on = depends_on
        self._value = None
        self.set(None, default)
        self.active_func = active_func
        self.name = None  # will be set on runtime
        self.optional = optional
        self.msg = ""

    def get(self, obj=None):
        return self._value

    def set(self, obj, value):
        self._value = value

    def convert_from_prompt(self, value):
        return value

    def test(self, value):
        if value is None:
            return True
        return self._test(value)

    def _test(self, value):
        return True

    def load(self, value):
        if not value:
            return
        self._value = self._load(value)

    def _load(self, value):
        return value

    def save(self):
        if self._value is None:
            return None

        if self.test(self._value):
            return self._save()
        raise ValueError("Tried to save an invalid ConfigObject")

    def _save(self):
        return self._value

    def is_active(self):
        return self.active_func() and all([x.is_set() for x in self.depends_on])

    def is_set(self):
        return self._value is not None or self.optional

    def is_valid(self):
        if not self.is_active():
            return True
        if self.is_set() and self.test(self._value):
            return True
        return False

    def _middle_prompt(self):
        return ""

    def _get_current(self):
        return f" ({self._save()})" if self.is_valid() else ""

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
            return f" ({censored})"
        return ""

    def get_user_prompt(self):
        return f"Please enter your password{self._get_current()} (password is not shown): "


class ConfigBool(ConfigString):
    TYPE = bool

    def _load(self, value):
        return "y" in value

    def _save(self):
        return "yes" if self._value else "no"

    def convert_from_prompt(self, value):
        return "y" in value

    def get_user_prompt(self):
        string_value = "yes" if self.get() else "no"
        current = f" ({string_value}) (yes/no)"

        return f"Please enter the bool for {self.name}{current}: "


class ConfigOption(ConfigString):
    def __init__(self, options, default=None, **kwargs):
        if default is not None and default not in options:
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
            logger.warning(f"Could not load value from {self.name}. Using empty list")
            return []

        return [x.strip() for x in value[1:-1].split(",") if x.strip()]

    def convert_from_prompt(self, value):
        value = value.strip()
        if value and (value[0] != "[" or value[-1] != "]"):
            self.msg = "Not valid format"
            return None
        return self._load(value)

    def _test(self, value):
        if not isinstance(value, list):
            raise ValueError("Value must be a list")
        return True

    def _middle_prompt(self):
        return " (format: [value1,value2,etc..] (empty is []))"
