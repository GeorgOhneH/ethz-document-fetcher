import base64
import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from settings.values.string import ConfigString

logger = logging.getLogger(__name__)


class CheckBox(QCheckBox):
    def get_value(self):
        return self.isChecked()

    def set_value(self, value):
        self.setChecked(value)


class ConfigBool(ConfigString):
    def init_widget(self):
        widget = CheckBox(self.name)
        widget.set_value(self.get())
        return widget

    def _load(self, value):
        return value.lower() in ('yes', 'true', 't', 'y', '1')

    def _save(self):
        return "yes" if self._value else "no"

    def set_parser(self, parser):
        feature_parser = parser.add_mutually_exclusive_group(required=False)
        feature_parser.add_argument(f'--{self.name}', dest=self.name, action='store_true')
        feature_parser.add_argument(f'--no-{self.name}', dest=self.name, action='store_false')
        parser.set_defaults(**{self.name: None})

    def convert_from_prompt(self, value):
        return self._load(value)

    def get_user_prompt(self):
        string_value = "yes" if self.get() else "no"
        current = f" ({string_value}) (yes/no)"

        return f"Please enter the bool for {self.name}{current}: "
