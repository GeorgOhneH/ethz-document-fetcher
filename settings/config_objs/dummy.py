import logging

from PyQt5.QtWidgets import *

from settings.config_objs.string import ConfigString, AbstractConfigWidget

logger = logging.getLogger(__name__)


class Dummy(QWidget, AbstractConfigWidget):
    def __init__(self, config_obj):
        super().__init__()
        self.config_obj = config_obj
        self.data_changed_signal = None

    def get_value(self):
        return self.config_obj.get()

    def set_value(self, value):
        pass


class ConfigDummy(ConfigString):
    def __init__(self):
        super().__init__(optional=True)

    def init_widget(self):
        return Dummy(self)

    def _load(self, value):
        raise NotImplementedError()

    def _save(self):
        raise NotImplementedError()
