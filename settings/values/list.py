import base64
import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from settings.values.string import ConfigString, LineEdit

logger = logging.getLogger(__name__)


class ListLineEdit(LineEdit):
    def get_value(self):
        raw = super().get_value()
        return [x.strip() for x in raw.split(",") if x.strip()]

    def set_value(self, value):
        super(ListLineEdit, self).set_value(", ".join(value))


class ConfigList(ConfigString):
    def init_widget(self):
        return ListLineEdit(self)

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

    def set_parser(self, parser):
        parser.add_argument(f'--{self.name}', nargs='*')

    def _middle_prompt(self):
        return " (format: [value1,value2,etc..] (empty is []))"
