import logging

from PyQt5.QtWidgets import *

from settings.config_objs.string import ConfigString, AbstractConfigWidget

logger = logging.getLogger(__name__)


class CheckBox(QCheckBox, AbstractConfigWidget):
    def __init__(self, config_obj):
        super().__init__(config_obj.get_gui_name())
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.config_obj = config_obj
        self.data_changed_signal = self.stateChanged

    def get_value(self):
        return self.isChecked()

    def set_value(self, value):
        if value is not None:
            self.setChecked(value)


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
