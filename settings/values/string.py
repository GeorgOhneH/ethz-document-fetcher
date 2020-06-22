import base64
import logging
import copy

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from settings.values.constants import NotSet

logger = logging.getLogger(__name__)


class LineEdit(QWidget):
    def __init__(self, config_obj):
        super().__init__()
        self.config_obj = config_obj

        self.line_edit = QLineEdit()
        self.data_changed_signal = self.line_edit.textChanged
        if config_obj.get() is not None:
            self.set_value(config_obj.get())

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.addWidget(QLabel(f"{config_obj.get_gui_name()}: "))
        self.layout.addWidget(self.line_edit)
        self.setLayout(self.layout)

    def get_value(self):
        value = self.line_edit.text().strip()
        if value == "":
            return None
        return value

    def set_value(self, value):
        if value is not None:
            self.line_edit.setText(str(value))


class ConfigString(object):
    def __init__(self, default=None, active_func=lambda: True, depends_on=None, optional=False, gui_name=None):
        if depends_on is None:
            depends_on = []
        self.depends_on = depends_on
        self.default = default
        self.gui_name = gui_name
        self._value = None
        self.active_func = active_func
        self.name = None  # will be set on runtime
        self.optional = optional
        self.msg = ""
        self._buffer = None
        self.widget = None
        self.observers = []
        self.set(default)

    def get_widget(self):
        if self.widget is None:
            self.widget = self.init_widget()
        return self.widget

    def init_widget(self):
        return LineEdit(self)

    def get(self):
        return self._get()

    def _get(self):
        return self._value

    def get_gui_name(self):
        if self.gui_name is not None:
            return self.gui_name
        return self.name

    def set(self, value):
        self._set(value)

    def _set(self, value):
        self._value = value

    def add_observer(self, func):
        self.observers.append(func)

    def set_from_widget(self):
        value = self.widget.get_value()
        self.set(value)

    def is_valid_from_widget(self):
        value = self.widget.get_value()
        return self.is_valid(value)

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

    def is_active(self, value=NotSet):
        if value is NotSet:
            value = self._value
        return self.active_func() and all([x.is_set(value) for x in self.depends_on])

    def is_set(self, value=NotSet):
        if value is NotSet:
            value = self._value
        if isinstance(value, str) and value == "":
            value = None
        return value is not None or self.optional

    def is_valid(self, value=NotSet):
        if value is NotSet:
            value = self._value
        if not self.is_active(value):
            return True
        if not self.is_set(value):
            self.msg = "Can not be empty"
            return False
        if not self.test(value):
            return False
        return True

    def set_parser(self, parser):
        parser.add_argument(f"--{self.name}")

    def _middle_prompt(self):
        return ""

    def _get_current(self):
        return f" ({self._save()})" if self.is_valid() else ""

    def get_user_prompt(self):
        return f"Please enter the value for {self.name}{self._middle_prompt()}{self._get_current()}: "

    def update_widget(self):
        self.widget.set_value(self.get())

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if v is self.widget:
                setattr(result, k, v)
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result
