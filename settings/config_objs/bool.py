import logging

from PyQt5.QtWidgets import *

from settings.config_objs.string import ConfigString, AbstractConfigWidget

logger = logging.getLogger(__name__)


class CheckBox(QWidget, AbstractConfigWidget):
    def __init__(self, config_obj):
        super().__init__()
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.check_box = QCheckBox(config_obj.get_gui_name())
        self.layout.addWidget(self.check_box)
        self.config_obj = config_obj
        self.data_changed_signal = self.check_box.stateChanged
        self.setContentsMargins(0, 3, 0, 3)

    def get_value(self):
        return self.check_box.isChecked()

    def set_value(self, value):
        if value is not None:
            self.check_box.setChecked(value)


class ConfigBool(ConfigString):
    def init_widget(self):
        widget = CheckBox(self)
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
