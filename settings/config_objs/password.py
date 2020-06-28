import base64
import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from settings.config_objs.string import ConfigString, LineEdit

logger = logging.getLogger(__name__)


class ConfigPassword(ConfigString):
    def init_widget(self):
        widget = super(ConfigPassword, self).init_widget()
        widget.line_edit.setEchoMode(QLineEdit.Password)
        return widget

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
