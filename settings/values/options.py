import base64
import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from settings.values.string import ConfigString

logger = logging.getLogger(__name__)


class ComboBox(QWidget):
    def __init__(self, name, options, default):
        super().__init__()
        self.combo_box = QComboBox()
        self.combo_box.setPlaceholderText("------")
        self.combo_box.addItems(options)
        if default is not None:
            self.set_value(default)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setAlignment(Qt.AlignLeft)
        self.setLayout(self.layout)
        self.layout.addWidget(QLabel(f"{name}: "))
        self.layout.addWidget(self.combo_box)

    def get_value(self):
        self.combo_box.currentText()

    def set_value(self, value):
        self.combo_box.setCurrentText(value)


class ConfigOptions(ConfigString):
    def __init__(self, options, default=None, **kwargs):
        if default is not None and default not in options:
            raise ValueError("default not in options")
        super().__init__(default=default, **kwargs)
        self.options = options

    def init_widget(self):
        return ComboBox(self.name, self.options, self.get())

    def _test(self, value):
        if value in self.options:
            return True
        self.msg = f"please enter a value from these options: {self.options}"
        return False

    def set_parser(self, parser):
        parser.add_argument(f"--{self.name}", choices=self.options)

    def get_user_prompt(self):
        return f"Please enter the value for the {self.name} (options: {self.options}){self._get_current()}: "

