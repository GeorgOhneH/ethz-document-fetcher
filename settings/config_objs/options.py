import base64
import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from settings.config_objs.string import ConfigString, AbstractConfigWidget

logger = logging.getLogger(__name__)


class ComboBox(QWidget, AbstractConfigWidget):
    PLACE_HOLDER_TEXT = "------"

    def __init__(self, config_obj):
        super().__init__()
        self.config_obj = config_obj
        self.combo_box = QComboBox()
        self.data_changed_signal = self.combo_box.currentTextChanged
        self.combo_box.setPlaceholderText(self.PLACE_HOLDER_TEXT)
        self.combo_box.addItems(config_obj.options)
        if config_obj.get() is not None:
            self.set_value(config_obj.get())
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setAlignment(Qt.AlignLeft)
        self.setLayout(self.layout)
        self.layout.addWidget(QLabel(f"{config_obj.name}: "))
        self.layout.addWidget(self.combo_box)

    def get_value(self):
        text = self.combo_box.currentText()
        if text == self.PLACE_HOLDER_TEXT:
            return None
        return self.combo_box.currentText()

    def set_value(self, value):
        print(value)
        if value is None:
            self.combo_box.setCurrentIndex(-1)
        else:
            self.combo_box.setCurrentText(value)


class ConfigOptions(ConfigString):
    def __init__(self, options, default=None, **kwargs):
        if default is not None and default not in options:
            raise ValueError("default not in options")
        self.options = options
        super().__init__(default=default, **kwargs)

    def init_widget(self):
        return ComboBox(self)

    def _test(self, value):
        if value not in self.options:
            raise ValueError(f"Not one of the options: {self.options}")

    def reset_widget(self):
        print("RESET")
        super(ConfigOptions, self).reset_widget()

    def set_parser(self, parser):
        parser.add_argument(f"--{self.name}", choices=self.options)
