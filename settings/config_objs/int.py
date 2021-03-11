import logging

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from settings.config_objs.string import ConfigString, AbstractConfigWidget

logger = logging.getLogger(__name__)


class SpinBox(QWidget, AbstractConfigWidget):
    def __init__(self, config_obj):
        super().__init__()
        self.config_obj = config_obj
        self.spin_box = QSpinBox()
        self.spin_box.setMaximum(int(config_obj.maximum))
        self.spin_box.setMinimum(int(config_obj.minimum))
        self.data_changed_signal = self.spin_box.valueChanged
        if config_obj.get() is not None:
            self.set_value(config_obj.get())
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignLeft)
        self.setLayout(self.layout)
        self.layout.addWidget(QLabel(f"{config_obj.get_gui_name()}: "))
        self.layout.addWidget(self.spin_box)

    def get_value(self):
        return self.spin_box.value()

    def set_value(self, value):
        if value is None:
            return
        self.spin_box.setValue(value)


class ConfigInt(ConfigString):
    def __init__(self, minimum=-1e8, maximum=1e8, **kwargs):
        super().__init__(**kwargs)
        self.minimum = int(minimum)
        self.maximum = int(maximum)

    def init_widget(self):
        return SpinBox(self)

    def _load(self, value):
        return int(value)

    def _save(self):
        return str(self._value)

    def _test(self, value, from_widget):
        if not isinstance(value, int):
            raise ValueError("Not int")
        if value < self.minimum:
            raise ValueError("To Small")
        if value > self.maximum:
            raise ValueError("To Big")

    def set_parser(self, parser):
        parser.add_argument(f"--{self.name.replace('_', '-')}", type=int)
